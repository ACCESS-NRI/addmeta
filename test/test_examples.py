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

import os
from pathlib import Path
import pdb
import pytest
import shlex
import shutil

import jinja2

from addmeta import cli
from common import runcmd, get_meta_data_from_file, make_nc as make_nc_common, make_env_data, payu_run_id

@pytest.fixture
def make_nc(request):
    subdir = request.param
    wd = Path('test/examples/') / subdir
    ncfilename = wd / 'test.nc'
    cmd = f'ncgen -o {ncfilename} test/test.cdl'
    runcmd(cmd)
    yield ncfilename
    for f in wd.glob('**/*.nc'):
        f.unlink()
    for f in wd.glob('subdir*'):
        f.rmdir()
    for f in wd.glob('addmetalist_template'):
        f.unlink()


@pytest.mark.parametrize('make_nc', ['ocean'], indirect=True)
@pytest.mark.parametrize(
    "filenames,expected",
    [
        pytest.param(
            ['subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc',
             'ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc',
             'oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc'],
            {
             'subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc': 
             {
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
                'keywords': 'global,access-esm1.6',
                'model_version': '2.1', 
                'frequency': '1monthly'
             },
             'ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc': {
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
                'keywords': 'global,access-esm1.6',
                'model_version': '2.1',
                'frequency': '1yearly'
             },
             'oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc':
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
                'keywords': 'global,access-esm1.6',
                'model_version': "2.1" ,
                'frequency': "1monthly" ,
             },
            },
            id="ocean" 
        ),
    ],
)
def test_filename_regex(make_nc, filenames, expected):

    wd = Path('test/examples/ocean')
    testfile = wd / 'test.nc'

    for filename in filenames:
        filepath = wd / filename
        os.makedirs(filepath.parent, exist_ok=True)
        shutil.copy(testfile, filepath)

    runcmd(rf"addmeta -v -c {wd}/addmetalist -v --fnregex='oceanbgc-\dd-(?P<variable>.*?)-(?P<frequency>.*?)-(?P<reduction>.*?)-??_\d+_\d+\.nc$'")

    for filename in filenames:
        filepath = wd / filename
        actual = get_meta_data_from_file(filepath)

        # Date created will be dynamic, so remove but make sure it exists
        assert( actual.pop('date_created') )
        assert( expected[filename] == actual )


@pytest.mark.parametrize('make_nc', ['ocean_datavars'], indirect=True)
@pytest.mark.parametrize(
    "filenames,expected",
    [
        pytest.param(
            ['subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc',
             'ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc',
             'oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc'],
            {
             'subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc': 
             {
                'filename': "ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc",
                'help': "I need somebody" ,
                'model_version': "2.1" ,
                'realm': "ocean" ,
                'frequency': "1monthly" ,
                'Publisher': "Will be overwritten",
                'model': "ACCESS-ESM1.6" ,
                'version': "1.1" ,
                'url': "https://github.com/ACCESS-NRI/access-esm1.5-configs.git" ,
                'keywords': 'global,access-esm1.6',
                'run_id': payu_run_id
             },
             'ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc': {
                'filename': "ocean-3d-power_diss_drag-1yearly-mean-ym_0792_07.nc",
                'help': "I need somebody" ,
                'model_version': "2.1" ,
                'realm': "ocean" ,
                'frequency': "1yearly" ,
                'Publisher': "Will be overwritten",
                'model': "ACCESS-ESM1.6" ,
                'version': "1.1" ,
                'url': "https://github.com/ACCESS-NRI/access-esm1.5-configs.git" ,
                'keywords': 'global,access-esm1.6',
                'run_id': payu_run_id
             },
             'oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc': {
                'filename': "oceanbgc-3d-zprod_gross-1monthly-mean-ym_0792_01.nc" ,
                'help': "I need somebody" ,
                'model_version': "2.1" ,
                'realm': "ocean" ,
                'frequency': "1monthly" ,
                'Publisher': "Will be overwritten",
                'model': "ACCESS-ESM1.6" ,
                'version': "1.1" ,
                'url': "https://github.com/ACCESS-NRI/access-esm1.5-configs.git" ,
                'keywords': 'global,access-esm1.6',
                'run_id': payu_run_id
             },
            },
            id="ocean" 
        ),
    ],
)
def test_filename_regex_datavars(make_nc, make_env_data, filenames, expected):

    wd = Path('test/examples/ocean_datavars')
    testfile = wd / 'test.nc'

    for filename in filenames:
        filepath = wd / filename
        os.makedirs(filepath.parent, exist_ok=True)
        shutil.copy(testfile, filepath)

    runcmd(rf"addmeta -v -c {wd}/addmetalist -v --fnregex='oceanbgc-\dd-(?P<variable>.*?)-(?P<frequency>.*?)-(?P<reduction>.*?)-??_\d+_\d+\.nc$'", env={'TESTDIR': str(wd.absolute())})

    for filename in filenames:
        filepath = wd / filename
        actual = get_meta_data_from_file(filepath)

        # Date created will be dynamic, so remove but make sure it exists
        assert( actual.pop('date_created') )
        assert( expected[filename] == actual )

@pytest.mark.parametrize('make_nc', ['ocean'], indirect=True)
@pytest.mark.parametrize(
    "filenames,expected",
    [
        pytest.param(
            ['subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc'],
            {
             'subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc': 
             {
                'contact': 'Add your name here',
                'email': 'Add your email address here',
                'frequency': '1monthly',
                'help': 'I need somebody',
                'keywords': 'global,access-esm1.6',
                'license': 'CC-BY-4.0',
                'model': 'ACCESS-ESM1.6',
                'model_version': '2.1',
                'nominal_resolution': '100 km',
                'Publisher': 'Will be overwritten',
                'realm': 'ocean',
                'reference': 'https://doi.org/10.1071/ES19035',
                'url': 'https://github.com/ACCESS-NRI/access-esm1.5-configs.git',
                'version': '1.1',
             },
            },
            id="ocean" 
        ),
    ],
)
def test_filename_regex_absolute(make_nc, filenames, expected):

    wd = Path('test/examples/ocean').absolute()
    testfile = wd / 'test.nc'

    for filename in filenames:
        filepath = wd / filename
        os.makedirs(filepath.parent, exist_ok=True)
        shutil.copy(testfile, filepath)

    cmdfile = wd / 'addmetalist_template'

    with open(cmdfile.with_suffix('.j2'), 'r') as template, open(cmdfile, 'w') as output:
        output.write(jinja2.Template(template.read()).render(examples_ocean_dir=wd.parent))

    # Call function directly as this doesn't require any complicated commandline parsing
    cli.main(cli.main_parse_args(shlex.split(f"-c {cmdfile} -v")))

    for filename in filenames:
        filepath = wd / filename
        actual = get_meta_data_from_file(filepath)

        # Date created will be dynamic, so remove but make sure it exists
        assert( actual.pop('date_created') )
        assert( expected[filename] == actual )

@pytest.mark.parametrize('make_nc', ['ocean'], indirect=True)
@pytest.mark.parametrize(
    "filenames,expected",
    [
        pytest.param(
            ['subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc'],
            {
             'subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc': 
             {
                'contact': 'Add your name here',
                'date_created': 'right now',
                'email': 'Add your email address here',
                'frequency': '1monthly',
                'help': 'I need somebody',
                'keywords': 'global,access-esm1.6',
                'license': 'CC-BY-4.0',
                'model': 'ACCESS-ESM1.6',
                'model_version': '2.1',
                'nominal_resolution': '100 km',
                'Publisher': 'Will be overwritten',
                'realm': 'ocean',
                'reference': 'https://doi.org/10.1071/ES19035',
                'url': 'https://github.com/ACCESS-NRI/access-esm1.5-configs.git',
                'version': '1.1',
             },
            },
            id="ocean" 
        ),
    ],
)
def test_filename_regex_sorted(make_nc, filenames, expected):

    wd = Path('test/examples/ocean')
    testfile = wd / 'test.nc'

    for filename in filenames:
        filepath = wd / filename
        os.makedirs(filepath.parent, exist_ok=True)
        shutil.copy(testfile, filepath)

    runcmd(rf"addmeta -c {wd}/addmetalist -v --sort --fnregex='oceanbgc-\dd-(?P<variable>.*?)-(?P<frequency>.*?)-(?P<reduction>.*?)-??_\d+_\d+\.nc$'")

    for filename in filenames:
        filepath = wd / filename
        actual = get_meta_data_from_file(filepath)

        # Date created will be dynamic, so adjust its value
        actual['date_created'] = expected[filename]['date_created']

        # Confirm contents are intact
        assert expected[filename] == actual

        # Confirm order is as expected
        assert list(expected[filename].keys()) == list(actual.keys())

@pytest.mark.parametrize(
    "metadata_files_lists,expected",
    [
        pytest.param(
            # Try with just one metadata file
            [['test/meta_simple1.yaml']],
            {
                'unlikelytobeoverwritten': "total rubbish",
                'Publisher': "Will be overwritten",
                'a': 'ay'
            }
        ),
        pytest.param(
            # Try with two metadata files in the same file
            [['test/meta_simple1.yaml', 'test/meta_simple2.yaml']],
            {
                'unlikelytobeoverwritten': "total rubbish",
                'Publisher': "Will be overwritten",
                'a': 'ay',
                'b': 'bee'
            }
        ),
        pytest.param(
            # Try with two metadata files in different files
            [['test/meta_simple1.yaml'], ['test/meta_simple2.yaml']],
            {
                'unlikelytobeoverwritten': "total rubbish",
                'Publisher': "Will be overwritten",
                'a': 'ay',
                'b': 'bee'
            }
        ),
        pytest.param(
            # Try with three files split over two files
            [['test/meta_simple1.yaml'], ['test/meta_simple2.yaml', 'test/meta_simple3.yaml']],
            {
                'unlikelytobeoverwritten': "total rubbish",
                'Publisher': "Will be overwritten",
                'a': 'ay',
                'b': 'bee',
                'c': 'cee'
            }
        ),
    ]
)
def test_multiple_metadata_files(tmp_path, make_nc_common, metadata_files_lists, expected):
    testfile = make_nc_common
    
    # Write list of metadata files to file
    filelist_paths = []
    for i, metadata_files_list in enumerate(metadata_files_lists):
        filelist_path = f'{tmp_path}/filelist_{i}'
        with open(filelist_path, 'w') as f:
            for metadata_file in metadata_files_list:
                metadata_path = Path(metadata_file)
                f.write(f"{metadata_path.absolute()}\n")
        
        filelist_paths.append(filelist_path)

    assert len(filelist_paths) > 0, "Test requires at least one metadata file"
    filelist_str = " -l ".join(filelist_paths)

    cmd_str = f"addmeta -v -l {filelist_str} {testfile}"

    runcmd(cmd_str)

    actual = get_meta_data_from_file(testfile)

    # Confirm contents are intact
    assert expected == actual


def test_history_creation(tmp_path, make_nc_common):
    testfile = make_nc_common
    runcmd(rf"addmeta -v --update-history {testfile}")

    actual = get_meta_data_from_file(testfile)

    history_lines = actual['history'].split('\n')

    assert len(history_lines) == 1

def test_history_update(tmp_path, make_nc_common):
    testfile = make_nc_common
    runcmd(rf"addmeta -v --update-history {testfile}")
    runcmd(rf"addmeta -v --update-history {testfile}")

    actual = get_meta_data_from_file(testfile)

    history_lines = actual['history'].split('\n')

    assert len(history_lines) == 2

@pytest.mark.parametrize('make_nc', ['ocean'], indirect=True)
@pytest.mark.parametrize(
    "filenames,expected",
    [
        pytest.param(
            ['subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc'],
            {
             'subdir1/ocean-2d-wind_power_u-1monthly-mean-ym_0792_01.nc': 
             {
                'command_line_arg_data_1': '1',
                'command_line_arg_data_2': 'Command line argument string',
                'contact': 'Add your name here',
                'date_created': 'right now',
                'email': 'Add your email address here',
                'frequency': '1monthly',
                'help': 'I need somebody',
                'keywords': 'global,access-esm1.6',
                'license': 'CC-BY-4.0',
                'model': 'ACCESS-ESM1.6',
                'model_version': '2.1',
                'nominal_resolution': '100 km',
                'Publisher': 'Will be overwritten',
                'realm': 'ocean',
                'reference': 'https://doi.org/10.1071/ES19035',
                'url': 'https://github.com/ACCESS-NRI/access-esm1.5-configs.git',
                'version': '1.1',
             },
            },
            id="ocean" 
        ),
    ],
)
def test_filename_datavar(make_nc, filenames, expected):
    """Test that the datavar command line arguments are correctly substituted in the metadata files."""
    wd = Path('test/examples/ocean')
    testfile = wd / 'test.nc'

    for filename in filenames:
        filepath = wd / filename
        os.makedirs(filepath.parent, exist_ok=True)
        shutil.copy(testfile, filepath)

    runcmd(rf"addmeta -c {wd}/addmetalist -m {wd}/meta_argdata.yaml -v --sort --datavar cmd1=1 --datavar cmd2='Command line argument string'")

    for filename in filenames:
        filepath = wd / filename
        actual = get_meta_data_from_file(filepath)

        # Date created will be dynamic, so adjust its value
        actual['date_created'] = expected[filename]['date_created']

        # Confirm contents are intact
        assert expected[filename] == actual

        # Confirm order is as expected
        assert list(expected[filename].keys()) == list(actual.keys())
