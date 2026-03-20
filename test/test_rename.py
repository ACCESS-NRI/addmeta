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

def get_var_names(ncfile):
    with netCDF4.Dataset(ncfile, 'r') as ds:
        return ds.variables.keys()

def get_dim_names(ncfile):
    with netCDF4.Dataset(ncfile, 'r') as ds:
        return ds.dimensions.keys()

@pytest.mark.parametrize(
    "name_tuples",
    [
        [("Times", "time")],
        [("Times", "times")],
        [("Times", "quiteadifferentname99")],
        [("Times", "_underscore")],
        [("Times", "time"), ("temp", "temperature")],
    ]
)
def test_rename_vars(make_nc, name_tuples):
    """
    Rename a list of variables given as a list of (old_name, new_name)
    """
    cmd_names = [f"{old_name} {new_name}" for old_name, new_name in name_tuples]
    cmd_str = "--rename-var " + " --rename-var ".join(cmd_names)

    runcmd(f"addmeta {cmd_str} {make_nc}")

    var_names = get_var_names(make_nc)

    for old_name, new_name in name_tuples:
        assert old_name not in var_names
        assert new_name in var_names

@pytest.mark.parametrize(
    "name_tuples",
    [
        [("x", "ex")],
        [("y", "thisisaverylongdimname")],
        [("Times", "times")],
        [("x", "_underscore")],
        [("x", "ex"), ("Times", "time"), ("y", "why")],
    ]
)
def test_rename_dims(make_nc, name_tuples):
    """
    Rename a list of dims given as a list of (old_name, new_name)
    """
    cmd_names = [f"{old_name} {new_name}" for old_name, new_name in name_tuples]
    cmd_str = "--rename-dim " + " --rename-dim ".join(cmd_names)

    runcmd(f"addmeta {cmd_str} {make_nc}")

    dim_names = get_dim_names(make_nc)

    for old_name, new_name in name_tuples:
        assert old_name not in dim_names
        assert new_name in dim_names
