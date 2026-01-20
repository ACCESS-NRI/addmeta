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

from pathlib import Path
import os
import shlex
import subprocess
import yaml

import netCDF4 as nc
import pytest

payu_run_id = '0d1e048'
    
def runcmd(cmd, rwd=None):
    """
    Run a command, print stderr to stdout and optionally run in working
    directory relative to the current directory
    """
    cwd = Path.cwd()
    if rwd is not None:
        cwd = str(cwd / rwd)
    subprocess.run(shlex.split(cmd),stderr=subprocess.STDOUT, cwd=cwd)

@pytest.fixture
def make_nc(tmp_path):
    ncfilename = f'{tmp_path}/test.nc'
    cmd = f"ncgen -o {ncfilename} test/test.cdl"
    runcmd(cmd)
    return ncfilename

@pytest.fixture
def make_env_data():
    env = dict(os.environ)
    env['PAYU_RUN_ID'] = payu_run_id
    fname = Path('test/examples/env.yaml')
    with open(fname, 'w') as outfile:
        yaml.dump(env, outfile)

    yield fname
    fname.unlink()

def get_meta_data_from_file(fname, var=None):

    metadict = {}
    rootgrp = nc.Dataset(fname, "r")
    if var is None:
        metadict = rootgrp.__dict__
    else:
        metadict = rootgrp.variables[var].__dict__
        
    rootgrp.close()

    return metadict
    
def dict1_in_dict2(dict1, dict2):

    for k,v in dict1.items():
        if k in dict2:
            if v != dict2[k]:
                return False
        else:
            return False

    return True