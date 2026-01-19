#!/usr/bin/env python

"""
Copyright 2025 ACCESS-NRI

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

import netCDF4 as nc
import pytest

from addmeta import read_yaml, read_metadata, add_meta, find_and_add_meta, isoformat
from common import runcmd, make_nc, get_meta_data_from_file

verbose = True

def test_read_templated_yaml():

    dict1 = read_metadata("test/meta_template.yaml")

    assert(dict1 == {
        'global': {
            'Publisher': 'ACCESS-NRI', 
            'Year': 2025,
            'filename': "{{ __file__.name }}",
            'size': "{{ __file__.size }}",
            'directory': "{{ __file__.parent }}",
            'fullpath': "{{ __file__.fullpath }}",
            'modification_time': "{{ __file__.mtime }}",
        }
        }
    )
           
def test_add_templated_meta(make_nc):
    dict1 = read_yaml("test/meta_template.yaml")

    size_before = str(Path(make_nc).stat().st_size)

    # Format mtime using our tweaked isoformat function
    mtime_before = isoformat(datetime.fromtimestamp(Path(make_nc).stat().st_mtime, tz=timezone.utc))

    find_and_add_meta([make_nc], dict1, {}, {})

    dict2 = get_meta_data_from_file(make_nc)

    ncfile_path = Path(make_nc).absolute()

    assert(dict2["Publisher"] == "ACCESS-NRI")
    assert(dict2["Year"] == 2025)
    assert(dict2["directory"] == str(ncfile_path.parent))
    assert(dict2["fullpath"]  == str(ncfile_path))
    assert(dict2["filename"]  == ncfile_path.name)
    # Can't use stat().st_size because size changes when metadata 
    # is added, so need to use saved value
    assert(dict2["size"] == size_before)
    assert(dict2["modification_time"] == mtime_before)

def test_undefined_meta(make_nc):

    dict1 = read_yaml("test/meta_undefined.yaml")

    # Missing template variable should throw a warning
    with pytest.warns(UserWarning, match="Skip setting attribute 'foo': 'bar' is undefined"):
        add_meta(make_nc, dict1, {})

    # Attribute using missing template variable should not be present in output file
    dict2 = get_meta_data_from_file(make_nc)
    assert( not 'foo' in dict2 )

@pytest.mark.parametrize(
    "ncfiles,metadata,fnregexs,expected",
    [
        pytest.param(
            [
                'access-om3.mom6.3d.temp.1day.mean.1900-01.nc', 
                'access-om3.cice.3d.salt.1mon.mean.1900-01.nc',
            ],
            {'global': {
                'Year': 2025,
                'unlikelytobeoverwritten': None,
                'Publisher': 'ACCESS-NRI',
                'model': '{{ __file__.model }}',
                'frequency': '{{ __file__.frequency }}',
                }, 
            },
            [
                r'.*access-om3\.(?P<model>.*?)\.', #\dd\..*?\..*',
                r'.*\.(?P<frequency>.*)\..*?\.\d+-\d+\.nc$',
            ],
            [
                {
                    'Year': 2025, 
                    'frequency': '1day',
                    'model': 'mom6',
                    'Publisher': 'ACCESS-NRI',
                },
                {
                    'Year': 2025, 
                    'frequency': '1mon',
                    'model': 'cice',
                    'Publisher': 'ACCESS-NRI',
                },
            ],
            id="access-om3" 
        ),
        pytest.param(
            [
                'ocean-3d-diff_cbt_wave-1yearly-mean-ym_0792_07.nc',
                'iceh-1monthly-mean_1181-03.nc',
            ],
            {'global': {
                'Year': 2025,
                'unlikelytobeoverwritten': None,
                'Publisher': 'ACCESS-NRI',
                'reduction': '{{ __file__.reduction }}',
                'frequency': '{{ __file__.frequency }}',
                'variable': '{{ __file__.variable }}',
                }, 
            },
            [
                r'.*ocean-\dd-(?P<variable>.*?)-(?P<frequency>.*?)-(?P<reduction>.*?)-\S\S_\d+_\d+\.nc$',
                r'.*iceh-(?P<frequency>\d.*?)-(?P<reduction>.*?)_\d{4}-\d{2}\.nc$',
            ],
            [
                {
                    'Year': 2025, 
                    'frequency': '1yearly',
                    'variable': 'diff_cbt_wave',
                    'reduction': 'mean',
                    'Publisher': 'ACCESS-NRI',
                },
                {
                    'Year': 2025, 
                    'frequency': '1monthly',
                    'reduction': 'mean',
                    'Publisher': 'ACCESS-NRI',
                },
            ],
            id="access-esm1.6.mom5.cice" 
        ),
        pytest.param(
            [
                'aiihca.pe-118104_dai.nc',
                'aiihca.pa-118106_mon.nc',
            ],
            {
                'global': 
                {
                    'Year': 2025,
                    'unlikelytobeoverwritten': None,
                    'Publisher': 'ACCESS-NRI',
                    'frequency': '{{ __file__.frequency }}',
                }, 
            },
            [
                r'^.*?\..*?-\d{6}_(?P<frequency>.*?).nc$',
                r'^.*?\..*?-\d{6}_(?P<frequency>.*?).nc$',
            ],
            [
                {'Year': 2025, 'Publisher': 'ACCESS-NRI', 'frequency': 'dai' },
                {'Year': 2025, 'Publisher': 'ACCESS-NRI', 'frequency': 'mon' },
            ],
            id="access-esm1p6.um" 
        ),
    ]
)
@pytest.mark.filterwarnings("ignore:Skip setting attribute \'variable\'")
def test_find_add_filename_metadata(make_nc, tmp_path, ncfiles, metadata, fnregexs, expected):
    
    # Make paths relative to test directory and make copy
    # of test.nc for each filename
    ncfiles = [str(tmp_path / Path(file)) for file in ncfiles]
    for file in ncfiles:
        runcmd(f'cp {make_nc} {file}')

    # Add metadata extracted from filename
    find_and_add_meta(ncfiles, metadata, {}, fnregexs)

    for (file, expectation) in zip(ncfiles, expected):
        assert expectation == get_meta_data_from_file(file)

@pytest.mark.parametrize(
    "metadata,expected",
    [
        pytest.param( # Test updating a variable's attr
            {
                'variables':
                {
                    'temp': {
                        'units': 'degK',
                    },
                }
            },
            {
                'variables': {
                    'temp': {
                        'units': "degK",
                        '_FillValue': 1.e+20,
                        'missing_value': 1.e+20,
                        'long_name': "Temperature",
                    }
                }
            },
        ),
        pytest.param( # Test setting attrs that depends on another attr
            {
                'global': 
                {
                    'a': 'a',
                    # 'b': '{{ a }}', no longer supported
                },
            },
            {
                'global': {
                    'unlikelytobeoverwritten': 'total rubbish',
                    'Publisher': "Will be overwritten",
                    'a': 'a',
                    # 'b': 'a',
                }
            },
        ),
        pytest.param( # Test setting attrs that depends on list attr
            {
                'global': 
                {
                    'a': ['1', '2', '3'],
                    # 'b': '{{ a }}', No longer supported
                },
            },
            {
                'global': {
                    'unlikelytobeoverwritten': 'total rubbish',
                    'Publisher': "Will be overwritten",
                    'a': '1,2,3',
                    # 'b': '1,2,3',
                }
            },
        ),
    ]
)
def test_add_variable_metadata(make_nc, metadata, expected):
    # Add metadata
    find_and_add_meta([make_nc], metadata, {}, [])

    # Confirm that the global metadata has been updated
    if 'global' in expected:
        assert expected['global'] == get_meta_data_from_file(make_nc)

    # Confirm that the variable metadata has been updated
    if 'variables' in expected:
        for varname, var_attrs in expected['variables'].items():
            assert var_attrs == get_meta_data_from_file(make_nc, var=varname)

def test_now(make_nc):
    """
    Test the built-in 'now' metadata template
    """
    metadata = {
        'global': 
        {
            'date_metadata_modified': '{{ __datetime__.now }}',
        },
    }

    # Add metadata
    find_and_add_meta([make_nc], metadata, {}, [])

    # Confirm that 'now' is isoformat-ed and close to the current time
    # fromisoformat doesn't support this format until python3.11
    now_str = get_meta_data_from_file(make_nc)['date_metadata_modified']
    meta_now = datetime.strptime(now_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    utc_now = datetime.now(timezone.utc)
    assert meta_now - utc_now < timedelta(minutes=1)
