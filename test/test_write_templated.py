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

from datetime import datetime
from pathlib import Path

import netCDF4 as nc
import pytest

from addmeta import read_yaml, dict_merge, combine_meta, add_meta, find_and_add_meta, skip_comments, list_from_file
from common import runcmd, make_nc, get_meta_data_from_file

verbose = True

def test_read_templated_yaml():

    dict1 = read_yaml("test/meta_template.yaml")

    assert(dict1 == {
        'global': {
            'Publisher': 'ACCESS-NRI', 
            'Year': 2025,
            'filename': "{{ name }}",
            'size': "{{ size }}",
            'directory': "{{ parent }}",
            'fullpath': "{{ fullpath }}",
            'modification_time': "{{ mtime }}",
        }
        }
    )
           
def test_add_templated_meta(make_nc):
    
    dict1 = read_yaml("test/meta_template.yaml")

    ncfile = 'test/test.nc'

    size_before = str(Path(ncfile).stat().st_size)
    mtime_before = datetime.fromtimestamp(Path(ncfile).stat().st_mtime).isoformat()

    add_meta(ncfile, dict1, {})

    dict2 = get_meta_data_from_file(ncfile)

    ncfile_path = Path(ncfile).absolute()

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

    ncfile = 'test/test.nc'

    # Missing template variable should throw a warning
    with pytest.warns(UserWarning, match="Skip setting attribute 'foo': 'bar' is undefined"):
        add_meta(ncfile, dict1, {})

    # Attribute using missing template variable should not be present in output file
    dict2 = get_meta_data_from_file(ncfile)
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
                'model': '{{ model }}',
                'frequency': '{{ frequency }}',
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
                'reduction': '{{ reduction }}',
                'frequency': '{{ frequency }}',
                'variable': '{{ variable }}',
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
                    'frequency': '{{ frequency }}',
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
def test_find_add_filename_metadata(make_nc, ncfiles, metadata, fnregexs, expected):
    
    # Make paths relative to test directory and make copy
    # of test.nc for each filename
    ncfiles = [str('test' / Path(file)) for file in ncfiles]
    for file in ncfiles:
        runcmd(f'cp test/test.nc {file}')

    # Add metadata extracted from filename
    find_and_add_meta(ncfiles, metadata, fnregexs)

    for (file, expectation) in zip(ncfiles, expected):
        assert expectation == get_meta_data_from_file(file)
        # Clean-up
        runcmd(f'rm {file}')

@pytest.mark.parametrize(
    "filename,metadata,expected",
    [
        pytest.param( # Test updating a variable's attr
            'variable_attr.nc',
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
        pytest.param( # Test setting iterative attrs
            'iterative_attr.nc',
            {
                'global': 
                {
                    'a': 'a',
                    'b': '{{ a }}',
                    'c': '{{ b }}',
                    'd': '{{ c }}',
                    'e': '{{ d }}',
                    'f': '{{ e }}',
                },
            },
            {
                'global': {
                    'unlikelytobeoverwritten': 'total rubbish',
                    'Publisher': "Will be overwritten",
                    'a': 'a',
                    'b': 'a',
                    'c': 'a',
                    'd': 'a',
                    'e': 'a',
                    'f': 'a',
                }
            },
        ),
    ]
)
def test_add_variable_metadata(make_nc, filename, metadata, expected):
    orig_filepath, new_filepath = make_nc, f"test/{filename}"
    runcmd(f'cp {orig_filepath} {new_filepath}')

    # Add metadata
    find_and_add_meta([new_filepath], metadata, [])

    # Confirm that the global metadata has been updated
    if 'global' in expected:
        assert expected['global'] == get_meta_data_from_file(new_filepath)

    # Confirm that the variable metadata has been updated
    if 'variables' in expected:
        for varname, var_attrs in expected['variables'].items():
            assert var_attrs == get_meta_data_from_file(new_filepath, var=varname)

    runcmd(f'rm {new_filepath}')

@pytest.mark.parametrize(
    "filename,metadata",
    [
        pytest.param( # Test updating a variable's attr
            'circular_attr.nc',
            {
                'global': 
                {
                    'a': '{{ b }}',
                    'b': '{{ a }}',
                },
            },
        ),
    ]
)
def test_circular_templates(make_nc, filename, metadata):
    orig_filepath, new_filepath = make_nc, f"test/{filename}"
    runcmd(f'cp {orig_filepath} {new_filepath}')

    # Add metadata
    with pytest.raises(ValueError, match="Unable to resolve all Jinja template values after \\d+ attempts."):
        find_and_add_meta([new_filepath], metadata, [])

    runcmd(f'rm {new_filepath}')
