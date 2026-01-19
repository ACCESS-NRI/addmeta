#!/usr/bin/env python


"""
Copyright 2026 ACCESS-NRI

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

import copy
import os
from pathlib import Path
import yaml

import pytest
import netCDF4 as nc

import addmeta
from addmeta import load_data_files


@pytest.fixture
def make_env_data():
    env = dict(os.environ)
    env['PAYU_RUN_ID'] = '0d1e048'
    fname = Path('test/examples/env.yaml')
    with open(fname, 'w') as outfile:
        yaml.dump(env, outfile)

    yield fname
    fname.unlink()

def test_read_datafile():

    dict1 = load_data_files(["test/examples/metadata.yaml"])

    assert( "metadata" in dict1 )

    assert( "contact" in dict1["metadata"])
    assert( "email" in dict1["metadata"])
    assert( "nominal_resolution" in dict1["metadata"])
    assert( "license" in dict1["metadata"])


def test_read_datafiles(make_env_data):

    dict1 = load_data_files([make_env_data, "test/examples/metadata.yaml"])

    assert( "metadata" in dict1 )
    assert( "env" in dict1 )

    assert( "PAYU_RUN_ID" in dict1["env"])
    assert( "SHELL" in dict1["env"])
