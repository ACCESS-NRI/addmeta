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
from addmeta import sort_attributes
import netCDF4

@pytest.mark.parametrize(
    "initial,expected",
    [
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
                'nominal_resolution': "100 km" ,
                'model': "ACCESS-ESM1.6" ,
                'model_version': "2.1" ,
                'Publisher': "Will be overwritten",
                'realm': "ocean" ,
                'reference': "https://doi.org/10.1071/ES19035" ,
                'version': "1.1" ,
                'url': "https://github.com/ACCESS-NRI/access-esm1.5-configs.git" ,
             }
        )
    ]
)
def test_sort(initial, expected):
    with netCDF4.Dataset('test.nc', 'w', diskless=True) as ds:
        ds.setncatts(initial)

        assert ds.ncattrs() == list(initial.keys())

        sort_attributes(ds)

        assert ds.ncattrs() == list(expected.keys())
