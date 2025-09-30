#!/usr/bin/env python

from __future__ import print_function


from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from warnings import warn

from jinja2 import Template, StrictUndefined, UndefinedError
import netCDF4 as nc
import yaml

# From https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if isinstance(dct.get(k), dict) and isinstance(v, Mapping):
            dict_merge(dct[k], v)
        else:
            dct[k] = v

def read_yaml(fname):
    """Parse yaml file and return a dict."""

    metadict = {}
    try:
        with open(fname, 'r') as yaml_file:
            metadict = yaml.safe_load(yaml_file)
    except Exception as e:
        print("Error loading {file}\n{error}".format(file=fname, error=e))

    # Check if this appears to be a plain key/value yaml file rather
    # than a structured file with 'global' and 'variables' keywords
    assume_global = True
    for key in ["variables", "global"]:
        if key in metadict and isinstance(metadict[key], dict):
            assume_global = False
            
    if assume_global:
        metadict = {"global": metadict}

    return metadict

def combine_meta(fnames):
    """Read multiple yaml files containing meta data and combine their
    dictionaries. The order of the files is the reverse order of preference, so
    files listed later overwrite fields from files list earlier"""

    allmeta = {}

    for fname in fnames:
        meta = read_yaml(fname)
        dict_merge(allmeta, meta)

    return allmeta

def add_meta(ncfile, metadict):
    """
    Add meta data from a dictionary to a netCDF file
    """

    # Generate some template variables from the 
    # file being processed
    template_vars = {}

    ncpath = Path(ncfile)
    ncpath_stat = ncpath.stat()
    for key in ["mtime", "size"]:
        template_vars[key] = getattr(ncpath_stat, 'st_'+key)

    template_vars['mtime'] = datetime.fromtimestamp(template_vars['mtime']).isoformat()

    # Pre-populate from pathlib API
    template_vars['parent'] = ncpath.absolute().parent
    template_vars['name'] = ncpath.name
    template_vars['fullpath'] = str(ncpath.absolute())

    rootgrp = nc.Dataset(ncfile, "r+")
    # Add metadata to matching variables
    if "variables" in metadict:
        for var, attr_dict in metadict["variables"].items():
            if var in rootgrp.variables:
                for attr, value in attr_dict.items():
                    set_attribute(rootgrp.variables[var], attr, value, template_vars)

    # Set global meta data
    if "global" in metadict:
        for attr, value in metadict['global'].items():
            set_attribute(rootgrp, attr, value, template_vars)

    rootgrp.close()

def set_attribute(group, attribute, value, template_vars):
    """
    Small wrapper to select to delete or set attribute depending 
    on value passed and expand jinja template variables
    """
    if value is None:
        if attribute in group.__dict__:
            group.delncattr(attribute)
    else:
        # Only valid to use jinja templates on strings
        if isinstance(value, str):
            try:
                value = Template(value, undefined=StrictUndefined).render(template_vars)
            except UndefinedError as e:
                warn(f"Skip setting attribute '{attribute}': {e}")
                return

        group.setncattr(attribute, value)

def find_and_add_meta(ncfiles, metafiles):
    """
    Add meta data from 1 or more yaml formatted files to one or more
    netCDF files
    """

    metadata = combine_meta(metafiles)

    for fname in ncfiles:
        add_meta(fname, metadata)
        
def skip_comments(file):
    """Skip lines that begin with a comment character (#) or are empty
    """
    for line in file:
        sline = line.strip()
        if not sline.startswith('#') and not sline == '':
            yield sline
    
def list_from_file(fname):
    with open(fname, 'rt') as f:
        filelist = [Path(fname).parent / file for file in skip_comments(f)]

    return filelist