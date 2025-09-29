#!/usr/bin/env python


"""
Copyright 2015 ARC Centre of Excellence for Climate Systems Science

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


from __future__ import print_function

import pytest
import sys
import os
import shutil
import subprocess
import shlex
import copy
import netCDF4 as nc
import six

from pathlib import Path

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

def test_read_yaml():
    if verbose:  print("\nIn test_read_yaml")

    dict1 = read_yaml("test/meta1.yaml")

    assert(dict1 == {
        'global': {
            'Publisher': 'ARC Centre of Excellence for Climate System Science', 
            'Year': 2017,
            'variables': 'temp, salt, salinity', 
            'global': "yes"
            }
        })

    dict2 = read_yaml("test/meta2.yaml")

    assert(dict2 == {'global': {'Publisher': 'ARC Centre of Excellence for Climate System Science (ARCCSS)', 'Credit': 'NCI'}})

    dictcombined = copy.deepcopy(dict2)

    dict_merge(dictcombined,dict1)

    assert(dictcombined == {
        'global': {
            'Publisher': 'ARC Centre of Excellence for Climate System Science', 
            'Year': 2017,
            'variables': 'temp, salt, salinity', 
            'Credit': 'NCI',
            'global': "yes"
            }
        })

    dictcombined_read = combine_meta(('test/meta2.yaml','test/meta1.yaml'))

    assert(dictcombined_read == dictcombined)

    # Unfortunately when yaml files are concatenated, subsequent values overwrite
    # previous entries, so this is equivalent to dict2
    dictcat = read_yaml("test/meta12.yaml")

    assert(dictcat == dict2)

def test_noglobal():
    if verbose:  print("\nIn test_noglobal")

    dict1 = read_yaml("test/meta1.yaml")
    dict2 = read_yaml("test/meta1_noglobal.yaml")

    assert(dict1 == dict2)

def test_metadata():

    metadata_dir = 'metadata'

    for root, dirs, files in os.walk(metadata_dir):
        for fname in files:
            path = os.path.join(root,fname)
            print("Reading {}".format(path))
            dict = read_yaml(path)

def test_skipcomments():

    fname = 'test/metalist'
    with open(fname, 'rt') as f:
        filelist = list(skip_comments(f))

    assert(filelist == ['meta1.yaml', 'meta2.yaml'])
    
def test_list_from_file():

    fname = 'test/metalist'
    filelist = list_from_file(fname)
    assert(filelist == [Path('test/meta1.yaml'), Path('test/meta2.yaml')])
    
def get_meta_data_from_file(fname,var=None):

    metadict = {}
    rootgrp = nc.Dataset(fname, "r")
    if var is None:
        metadict = rootgrp.__dict__
    else:
        metadict = rootgrp.variables[var].__dict__
        
    rootgrp.close()
    return metadict

def dict1_in_dict2(dict1, dict2):

    for k,v in six.iteritems(dict1):
        if k in dict2:
            if dict1[k] != dict2[k]:
                return False
        else:
            return False

    return True
           
def test_add_meta():

    ncfile = 'test/test.nc'
    
    dict1 = read_yaml("test/meta1.yaml")
    add_meta(ncfile, dict1)

    assert(dict1_in_dict2(dict1["global"], get_meta_data_from_file(ncfile)))

    dict1 = read_yaml("test/meta_var1.yaml")
    add_meta(ncfile, dict1)

    for var in dict1["variables"]:
        assert(dict1_in_dict2(dict1["variables"][var], get_meta_data_from_file(ncfile,var)))

def test_find_add_meta():
    
    ncfile = 'test/test.nc'

    delete_nc()
    make_nc()
    find_and_add_meta( [ncfile], ['test/meta2.yaml','test/meta1.yaml'])

    dict1 = read_yaml("test/meta1.yaml")
    assert(dict1_in_dict2(dict1["global"], get_meta_data_from_file(ncfile)))

    find_and_add_meta( [ncfile], ['test/meta_var1.yaml'] )

    dict1 = read_yaml("test/meta_var1.yaml")

    for var in dict1["variables"]:
        assert(dict1_in_dict2(dict1["variables"][var], get_meta_data_from_file(ncfile,var)))

def test_del_attributes():
    
    ncfile = 'test/test.nc'

    delete_nc()
    make_nc()

    attributes = get_meta_data_from_file(ncfile)
    assert( 'unlikelytobeoverwritten' in attributes )
    assert( 'Tiddly' not in attributes )

    attributes = get_meta_data_from_file(ncfile, 'temp')
    assert( '_FillValue' in attributes )
    assert( 'Tiddly' not in attributes )

    find_and_add_meta( [ncfile], ['test/meta_del.yaml'])

    attributes = get_meta_data_from_file(ncfile)
    assert( 'unlikelytobeoverwritten' not in attributes )
    assert( 'Tiddly' in attributes )
    assert( 'A long impressive sounding name' == attributes['Publisher'] )

    attributes = get_meta_data_from_file(ncfile, 'temp')
    assert( '_FillValue' not in attributes )
    assert( 'Tiddly' in attributes )
    assert( 'Kelvin' == attributes['units'] )

