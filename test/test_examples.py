#!/usr/bin/env python

"""
Copyright 2025 ACCESS-NRI

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

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

from pathlib import Path
import pytest

from common import runcmd, get_meta_data_from_file

@pytest.fixture
def make_nc():
    wd = 'test/examples/ocean'
    ncfilename = f'{wd}/test.nc'
    cmd = f'ncgen -o {ncfilename} test/test.cdl'
    runcmd(cmd)
    yield ncfilename
    files = [ str(p) for p in Path(wd).glob('*.nc') ]
    cmd = 'rm '+" ".join(files)
    runcmd(cmd)


@pytest.mark.parametrize(
    "filenames,expected",
    [
        pytest.param(
            ['ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc',
             'ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc',
             'oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc'],
            {
             'ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc': 
             {
                'unlikelytobeoverwritten': 'total rubbish', 
                'Publisher': 'Will be overwritten', 
                'contact': 'Add your name here', 
                'email': 'Add your email address here', 
                'realm': 'ocean', 
                'nominal_resolution': '100 km', 
                'reference': 'https://doi.org/10.1071/ES19035', 
                'license': 'CC-BY-4.0', 
                'model': 'ACCESS-ESM1.6', 
                'version': '1.1', 
                'url': 'https://github.com/ACCESS-NRI/access-esm1.5-configs.git', 
                'help': 'I need somebody', 
                'model_version': '2.1', 
                'frequency': '1monthly'
             },
             'ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc': {
                'unlikelytobeoverwritten': 'total rubbish', 
                'Publisher': 'Will be overwritten', 
                'contact': 'Add your name here', 
                'email': 'Add your email address here',
                'realm': 'ocean',
                'nominal_resolution': '100 km',
                'reference': 'https://doi.org/10.1071/ES19035',
                'license': 'CC-BY-4.0',
                'model': 'ACCESS-ESM1.6',
                'version': '1.1',
                'url': 'https://github.com/ACCESS-NRI/access-esm1.5-configs.git',
                'help': 'I need somebody',
                'model_version': '2.1',
                'frequency': '1yearly'
             },
             'oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc':
             {
                'unlikelytobeoverwritten': "total rubbish",
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
            },
            id="ocean" 
        ),
    ],
)
def test_filename_regex(make_nc, filenames, expected):

    wd = 'test/examples/ocean'

    for filename in filenames:
        filepath = f'{wd}/{filename}'
        runcmd(f'cp {wd}/test.nc {filepath}')

    runcmd("addmeta -c addmetalist -v --fnregex='^oceanbgc-\dd-(?P<variable>.*?)-(?P<frequency>.*?)-(?P<reduction>.*?)-??_\d+_\d+\.nc$'", wd)

    for filename in filenames:
        filepath = f'{wd}/{filename}'
        actual = get_meta_data_from_file(filepath)

        # Date created will be dynamic, so remove but make sure it exists
        assert( actual.pop('date_created') )
        assert( expected[filename] == actual )

