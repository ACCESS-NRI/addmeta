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
import yaml

from common import runcmd, make_nc

def get_var_names(ncfile):
    with netCDF4.Dataset(ncfile, 'r') as ds:
        return ds.variables.keys()

def get_dim_names(ncfile):
    with netCDF4.Dataset(ncfile, 'r') as ds:
        return ds.dimensions.keys()

def get_names(ncfile, var_or_dim):
    if var_or_dim == "variable":
        return get_var_names(ncfile)
    else:
        return get_dim_names(ncfile)

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
def test_rename_vars(tmp_path, make_nc, name_tuples):
    """
    Rename a list of variables given as a list of (old_name, new_name)
    """
    d = {
        "rename": {
            "variables": {k: v for k, v in name_tuples},
        }
    }

    meta_path = tmp_path / "meta.yaml"
    with open(meta_path, "w") as f:
        yaml.dump(d, f)

    runcmd(f"addmeta -m {meta_path} {make_nc}")

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
def test_rename_dims(tmp_path, make_nc, name_tuples):
    """
    Rename a list of dims given as a list of (old_name, new_name)
    """
    d = {
        "rename": {
            "dimensions": {k: v for k, v in name_tuples},
        }
    }

    meta_path = tmp_path / "meta.yaml"
    with open(meta_path, "w") as f:
        yaml.dump(d, f)

    runcmd(f"addmeta -m {meta_path} {make_nc}")

    dim_names = get_dim_names(make_nc)

    for old_name, new_name in name_tuples:
        assert old_name not in dim_names
        assert new_name in dim_names

@pytest.mark.parametrize(
    "var_or_dim", ["variable", "dimension"]
)
def test_rename_var_dim_missing(tmp_path, make_nc, var_or_dim):
    """
    Confirm that trying to rename a variable or dimension that doesn't exist
    does not fail.
    """
    old_name = "thisdoesntexist"
    new_name = "newname"
    d = {
        "rename": {
            f"{var_or_dim}s": {
                old_name: new_name
            },
        }
    }

    meta_path = tmp_path / "meta.yaml"
    with open(meta_path, "w") as f:
        yaml.dump(d, f)

    runcmd(f"addmeta -m {meta_path} {make_nc}")

    names = get_names(make_nc, var_or_dim)

    assert old_name not in names
    assert new_name not in names    
