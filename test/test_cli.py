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

from argparse import Namespace
import pytest
from unittest.mock import patch

import addmeta.cli
from common import runcmd

@pytest.fixture
def touch_nc():
    files =  ['ocean_1.nc', 'ocean_2.nc', 'ice_hourly.nc']
    runcmd('touch '+" ".join(files))
    yield files
    runcmd('rm '+" ".join(files))

def test_requirement_arguments():

    expected_msg = 'Error: no files specified'

    with pytest.raises(SystemExit, match=expected_msg):
        addmeta.cli.main_parse_args([])

@patch('addmeta.cli.main')
def test_cmdlinearg_from_file(mock_main, touch_nc):

    mock_main.return_value = True

    fname = "test/metacmdlineargs"

    args = [f"-c={fname}", f"-m=anotherfile"]

    assert addmeta.cli.main_parse_args(args) == True

    all_args = Namespace(metafiles=['anotherfile', 'meta1.yaml', 'meta2.yaml'], 
              metalist=None, 
              cmdlineargs=None, 
              fnregex=["'\\d{3]\\.'", "'(?:group\\d{3])\\.nc'"], 
              verbose=False, 
              sort=False,
              files=touch_nc[0:2])

    mock_main.assert_called_once_with(all_args)