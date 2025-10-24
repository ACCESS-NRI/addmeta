#!/usr/bin/env python

"""
Copyright 2025 ACCESS-NRI

author: Joshua Torrance <joshua.torrance@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License"),
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest
import netCDF4
import xarray

from addmeta import order_dict
from common import runcmd, get_meta_data_from_file, make_nc

@pytest.fixture
def make_xarray_nc():
    ncfilename = 'test/test_xarray.nc'
    with xarray.Dataset() as ds:
        # Duplicate the metadata created in make_nc
        ds.attrs = {
            'unlikelytobeoverwritten': "total rubbish",
            'Publisher': 'Will be overwritten',
        }
        ds.to_netcdf(ncfilename)

    yield ncfilename

    cmd = f"rm {ncfilename}"
    runcmd(cmd)

@pytest.mark.parametrize(
    "initial,expected",
    [
        pytest.param(
            {
                'b': 'b',
                'a': 'a',
                '1': 'one',
                'z': 'z',
                '_z': 'underscored keyname',
            },
            {
                '1': 'one',
                '_z': 'underscored keyname',
                'a': 'a',
                'b': 'b',
                'z': 'z',
            }
        ),
        pytest.param(
            {
                'Publisher': "Will be overwritten",
                'contact': "Add your name here" ,
                'email': "Add your email address here" ,
                'realm': "ocean" ,
                'nominal_resolution': "100 km" ,
                'reference': "https://doi.org/10.1071/ES19035" ,
                'license': "CC-BY-4.0" ,
                'model': "ACCESS-ESM1.6" ,
                'version': "1.1" ,
                'url': "https://github.com/ACCESS-NRI/access-esm1.5-configs.git" ,
                'help': "I need somebody" ,
                'model_version': "2.1" ,
                'frequency': "1monthly" ,
             },
             {
                'contact': "Add your name here" ,
                'email': "Add your email address here" ,
                'frequency': "1monthly" ,
                'help': "I need somebody" ,
                'license': "CC-BY-4.0" ,
                'model': "ACCESS-ESM1.6" ,
                'model_version': "2.1" ,
                'nominal_resolution': "100 km" ,
                'Publisher': "Will be overwritten",
                'realm': "ocean" ,
                'reference': "https://doi.org/10.1071/ES19035" ,
                'url': "https://github.com/ACCESS-NRI/access-esm1.5-configs.git" ,
                'version': "1.1" ,
             }
        )
    ]
)
def test_sort(initial, expected):
    final = order_dict(initial)
    assert list(final.keys()) == list(expected.keys())

@pytest.mark.parametrize("use_xarray", [True, False])
def test_sort_no_change(use_xarray, make_xarray_nc, make_nc):
    """
    Test that sorting an nc still works if no attrs are changed
    """
    # Getting the path is a bit fiddly using the fixtures
    ncpath =  make_xarray_nc if use_xarray else make_nc

    expected = {
        '_1': 'one',
        '_z': 'underscored',
        'a': 'ay',
        'b': 'bee',
        'Publisher': 'Will be overwritten',
        'unlikelytobeoverwritten': "total rubbish",
        'z': 'zed',
    }

    # Add the additiona metadata but don't sort
    runcmd(f"addmeta -m test/meta_sort1.yaml {ncpath}")
    
    # Check the metadata is NOT in order
    actual = get_meta_data_from_file(ncpath)
    assert list(actual.keys()) != list(expected.keys())

    # Add the same metadata (i.e. don't change contents) but sort this time
    runcmd(f"addmeta -m test/meta_sort1.yaml -s {ncpath}")

    # Check the metadata is now in order
    actual = get_meta_data_from_file(ncpath)
    assert list(actual.keys()) == list(expected.keys())

@pytest.mark.parametrize("use_xarray", [True, False])
def test_multisort(use_xarray, make_xarray_nc, make_nc):
    """
    Test applying metadata in multiple rounds with some sorting

    With the orginal method of sorting metadata this fails if the netCDF is created
    with xarray - specifically the final result is not correctly sorted
    """
    # Getting the path is a bit fiddly using the fixtures
    ncpath =  make_xarray_nc if use_xarray else make_nc

    # Add some metadata to the file
    runcmd(f"addmeta -m test/meta_sort1.yaml -v {ncpath}")

    # Add some more metadata to it
    runcmd(f"addmeta -m test/meta_sort2.yaml -v {ncpath}")

    # Add the second set of metadata again and sort
    runcmd(f"addmeta -m test/meta_sort2.yaml -v --sort {ncpath}")

    # Check the metadata is in order
    actual = get_meta_data_from_file(ncpath)

    expected = {
        '_1': 'one',
        '_a': 'underscore ay',
        '_z': 'underscored',
        'a': 'ay',
        'b': 'bee',
        'm': 'emm',
        'Publisher': 'Will be overwritten',
        'unlikelytobeoverwritten': "total rubbish",
        'z': 'zed',
        'zz': 'double zee',
    }

    # Check the contents are correct
    assert actual == expected
    # Check the order of the attrs is correct
    assert list(actual.keys()) == list(expected.keys())
