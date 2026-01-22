#!/usr/bin/env python

from __future__ import print_function


from collections import defaultdict
from collections.abc import Mapping
import copy
import csv
from datetime import datetime, timezone
import io
from pathlib import Path
import re
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
    """Open metadata yaml file and return a dict."""

    yamldict = {}
    with open(fname, 'r') as yaml_file:
        yamldict = yaml.safe_load(yaml_file)

    return yamldict 

def read_metadata(fname):

    metadict = read_yaml(fname)

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
        meta = read_metadata(fname)
        dict_merge(allmeta, meta)

    return allmeta

def get_file_metadata(filename):
    """Get file metadata and return as a dict"""

    ncpath = Path(filename)
    ncpath_stat = ncpath.stat()

    metadata = {key: getattr(ncpath_stat, 'st_'+key) for key in ["mtime", "size"]}

    # mtime should be a posix timestamp and thus in UTC
    metadata['mtime'] = isoformat(datetime.fromtimestamp(metadata['mtime'], tz=timezone.utc))

    # Pre-populate from pathlib API
    metadata['parent'] = ncpath.absolute().parent
    metadata['name'] = ncpath.name
    metadata['fullpath'] = str(ncpath.absolute())

    return metadata


def update_history_attr(group, history, verbose=False):
    """
    Update the history attribute with info on this invocation of addmeta.
    Create the history attribute if it doesn't exist yet.
    """
    if verbose: print(f"      + history: {history}")

    # Grab the previous history if it exists
    if "history" in group.ncattrs():
        history = "\n".join([group.getncattr("history"), history])

    # Update the attribute
    group.setncattr("history", history)


def add_meta(ncfile, metadict, template_vars, sort_attrs=False, history=None, verbose=False):
    """
    Add meta data from a dictionary to a netCDF file
    """

    rootgrp = nc.Dataset(ncfile, "r+")
    # Add metadata to matching variables
    if "variables" in metadict:
        for var, attr_dict in metadict["variables"].items():
            if var in rootgrp.variables:
                for attr, value in attr_dict.items():
                    set_attribute(rootgrp.variables[var], attr, value, template_vars)

    # Update (or create) the history attribute
    if history:
        update_history_attr(rootgrp, history, verbose=verbose)

    # Set global meta data
    if "global" in metadict:
        if sort_attrs:
            # Remove all global attributes, update with new attributes and then sort
            # | merges two dicts preferring keys from the right
            metadict['global'] = order_dict(delete_global_attributes(rootgrp) | metadict['global'])

        for attr, value in metadict['global'].items():
            set_attribute(rootgrp, attr, value, template_vars, verbose)

    rootgrp.close()

def match_filename_regex(filename, regexs, verbose=False):
    """
    Match a series of regexs against the filename and return a dict
    of jinja template variables
    """
    vars = {}

    for regex in regexs:
        match = re.search(regex, filename)
        if match:
            vars.update(match.groupdict())
    if verbose: print(f'    Matched following filename variables: {vars}')

    return vars

def array_to_csv(array):
    """
    Turn any list, tuple or set into a CSV string and return
    """
    with io.StringIO() as f:
        try:
            writer = csv.writer(f, doublequote=False, quoting=csv.QUOTE_MINIMAL, lineterminator='')
            writer.writerow(array)
        except csv.Error as e:
            # In case of failure return original unmodified
            warn(f"Serialisation failed for '{array}': {e}")
            return array
        else:
            return f.getvalue()

def set_attribute(group, attribute, value, template_vars, verbose=False):
    """
    Small wrapper to select, delete, or set attribute depending 
    on value passed and expand jinja template variables
    """
    if value is None:
        if attribute in group.__dict__:
            try:
                group.delncattr(attribute)
            except UndefinedError as e:
                warn(f"Could not delete attribute '{attribute}': {e}")
                return
            finally:
                if verbose: print(f"      - {attribute}")
    else:
        if isinstance(value, (list, tuple)):
            value = array_to_csv(value)

        # Only valid to use jinja templates on strings
        if isinstance(value, str):
            try:
                value = Template(value, undefined=StrictUndefined).render(template_vars)
            except UndefinedError as e:
                warn(f"Skip setting attribute '{attribute}': {e}")
                return
            finally:
                if verbose: print(f"      + {attribute}: {value}")

        group.setncattr(attribute, value)

def serialise_dict_values(dictionary):
    """Serialise any list or arrays values in a dictionary"""
    return {k: array_to_csv(v) if isinstance(v, (tuple, list)) else v for k, v in dictionary.items()}

def load_data_files(datafiles):
    """Load key/data from json files, and return a namespaced dict"""

    namespace_dict = {}

    for datafile in [Path(f) for f in datafiles]: 
        namespace_dict[datafile.stem] = serialise_dict_values(read_yaml(datafile))

    return namespace_dict

def find_and_add_meta(ncfiles, metadata, kwdata, fnregexs, sort_attrs=False, history=None, verbose=False):
    """
    Add meta data from 1 or more yaml formatted files to one or more
    netCDF files
    """

    template_vars = copy.deepcopy(kwdata)

    if verbose: print("Processing netCDF files:")
    for fname in ncfiles:
        if verbose: print(f"  {fname}")

        # Match supplied regex against filename and add metadata
        template_vars['__file__'] = match_filename_regex(fname, fnregexs, verbose)

        # Add file metadata
        template_vars['__file__'].update(get_file_metadata(fname))

        # Add special __datetime__.now template variable
        template_vars['__datetime__'] = {'now':  isoformat(datetime.now(timezone.utc)) }

        add_meta(
            fname,
            metadata,
            template_vars,
            sort_attrs=sort_attrs,
            history=history,
            verbose=verbose
        )
        
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

def delete_global_attributes(rootgrp):
    """
    Delete all global attributes and return as dict
    """
    deleted = {}

    for attr in rootgrp.ncattrs():
        deleted[attr] = rootgrp.getncattr(attr)
        rootgrp.delncattr(attr)
    
    return deleted

def order_dict(unsorted):
    """
    Return dict sorted by key, case-insensitive
    """
    return dict(sorted(unsorted.items(), key=lambda item: item[0].casefold()))

def isoformat(dt):
    """
    Return a string representing the datetime using ISO8601 with second precision
    and with 'Z' instead of '+00:00' for UTC/Zulu time.

    If timezone is not present or not '+00:00' then do nothing to the timezone.
    """
    return dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
