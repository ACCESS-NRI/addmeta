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
import os
from pathlib import Path
import shlex
import shutil
import sys
import subprocess
import copy

import netCDF4 as nc
import pytest

from addmeta import read_yaml, dict_merge, combine_meta, add_meta, find_and_add_meta, skip_comments, list_from_file

verbose = True

def runcmd(cmd):
    subprocess.check_call(shlex.split(cmd),stderr=subprocess.STDOUT)

def make_nc():
    cmd = "ncgen -o test/test.nc test/test.cdl"
    runcmd(cmd)

def delete_nc():
    cmd = "rm test/test.nc"
    runcmd(cmd)

def setup_module(module):
    if verbose: print ("setup_module      module:%s" % module.__name__)
    make_nc()
 
def teardown_module(module):
    if verbose: print ("teardown_module   module:%s" % module.__name__)
    delete_nc()

def get_meta_data_from_file(fname, var=None):

    metadict = {}
    rootgrp = nc.Dataset(fname, "r")
    if var is None:
        metadict = rootgrp.__dict__
    else:
        metadict = rootgrp.variables[var].__dict__
        
    rootgrp.close()

    return metadict
           
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
           
def test_add_templated_meta():

    
    dict1 = read_yaml("test/meta_template.yaml")

    ncfile = 'test/test.nc'

    size_before = str(Path(ncfile).stat().st_size)
    mtime_before = datetime.fromtimestamp(Path(ncfile).stat().st_mtime).isoformat()

    add_meta(ncfile, dict1)

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

