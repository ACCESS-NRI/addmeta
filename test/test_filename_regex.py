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

import pytest

from addmeta import match_filename_regex

@pytest.mark.parametrize(
    "filename,regexs,expected",
    [
        pytest.param(
            'access-om3.mom6.3d.agessc.1day.mean.1900-01.nc', 
            [r'.*\.(?P<frequency>.*)\.mean\.\d+-\d+\.nc$'], 
            {'frequency': '1day'}, 
            id="access-om3.mom6.frequency" 
        ),
        pytest.param(
            'access-om3.mom6.3d.agessc.1day.mean.1900-01.nc', 
            # 'access-om3.mom6.3d.agessc.rho.d2.1day.mean.1900-01.nc',
            [r'^access-om3\.(?P<model>.*?)\.\dd\.(?P<variable>.*?)\..*',
            r'.*\.(?P<frequency>.*)\..*?\.\d+-\d+\.nc$'],
            {'model': 'mom6', 'variable': 'agessc', 'frequency': '1day'}, 
            id="access-om3.mom6.model.variable.frequency.1" 
        ),
        pytest.param(
            'access-om3.mom6.3d.agessc.rho.d2.1day.mean.1900-01.nc',
            [r'^access-om3\.(?P<model>.*?)\.\dd\.(?P<variable>.*?)\..*',
            r'.*\.(?P<frequency>.*)\..*?\.\d+-\d+\.nc$'],
            {'model': 'mom6', 'variable': 'agessc', 'frequency': '1day'},
            id="access-om3.mom6.model.variable.frequency.2" 
        ),
        pytest.param(
            'ocean-3d-diff_cbt_wave-1yearly-mean-ym_0792_07.nc',
            [r'^ocean-\dd-(?P<variable>.*?)-(?P<frequency>.*?)-(?P<reduction>.*?)-\S\S_\d+_\d+\.nc$'],
            {'variable': 'diff_cbt_wave', 'frequency': '1yearly', 'reduction': 'mean'},
            id="access-esm1p6.mom5.variable.frequency.reduction.1" 
        ),
        pytest.param(
            'iceh-1monthly-mean_1181-03.nc',
            [r'^iceh-(?P<frequency>\d.*?)-(?P<reduction>.*?)_\d{4}-\d{2}\.nc$'],
            {'frequency': '1monthly', 'reduction': 'mean'},
            id="access-esm1p6.cice5.frequency.reduction.1" 
        ),
        pytest.param(
            'aiihca.pe-118104_dai.nc',
            [r'^.*?\..*?-\d{6}_(?P<frequency>.*?).nc$'],
            {'frequency': 'dai'},
            id="access-esm1p6.um.frequency.1" 
        ),
        pytest.param(
            'aiihca.pa-118106_mon.nc',
            [r'^.*?\..*?-\d{6}_(?P<frequency>.*?).nc$'],
            {'frequency': 'mon'},
            id="access-esm1p6.um.frequency.2" 
        ),
    ],
)
def test_filename_regex(filename, regexs, expected):

    assert( expected == match_filename_regex(filename, regexs) )

