#!/usr/bin/env python

from __future__ import print_function


from collections import defaultdict
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import re
from warnings import warn

from jinja2 import Template, StrictUndefined, UndefinedError, DebugUndefined
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

def add_meta(ncfile, metadict, template_vars, sort_attrs=False, verbose=False):
    """
    Add meta data from a dictionary to a netCDF file
    """

    # Generate some template variables from the 
    # file being processed

    ncpath = Path(ncfile)
    ncpath_stat = ncpath.stat()
    for key in ["mtime", "size"]:
        template_vars[key] = getattr(ncpath_stat, 'st_'+key)

    template_vars['mtime'] = datetime.fromtimestamp(template_vars['mtime']).isoformat()

    # Pre-populate from pathlib API
    template_vars['parent'] = ncpath.absolute().parent
    template_vars['name'] = ncpath.name
    template_vars['fullpath'] = str(ncpath.absolute())

    # Expand remaining jinja template variables
    metadict = resolve_template(metadict, template_vars, verbose=verbose)

    rootgrp = nc.Dataset(ncfile, "r+")
    # Add metadata to matching variables
    if "variables" in metadict:
        for var, attr_dict in metadict["variables"].items():
            if var in rootgrp.variables:
                for attr, value in attr_dict.items():
                    set_attribute(rootgrp.variables[var], attr, value, template_vars)

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

def resolve_template(metadict, template_vars, verbose=False):
    """
    Iteratively resolve the jinja variables in the attributes.
    """
    # Filter items by simply looking for jinja key substring
    filter_f = lambda s: '{{' in s if isinstance(s, str) else False
    # Resolve jinja templates and leave missing keys for later with DebugUndefined
    resolve_f = lambda s, t: Template(s, undefined=DebugUndefined).render(t)
    # Combine filter and resolve, note that template_vars is resolved when lambda is called not created
    filter_and_resolve = lambda d, t: {k: resolve_f(v, template_vars) for k, v in d.items() if filter_f(v)}

    # As a precaution against circular jinja keys use a loop limit
    LIMIT=100
    to_resolve = deepcopy(metadict)
    for _ in range(LIMIT):
        # Merge global meta data and template (favoring template)
        if 'global' in metadict:
            template_vars = metadict['global'] | template_vars

        # Don't add variable attributes to the template_vars since they're
        # comparatively complicated

        # Only resolve templates where there is a template
        resolved = {}
        resolved['global'] = filter_and_resolve(to_resolve.get('global', {}), template_vars)
        resolved['variables'] = {var: filter_and_resolve(var_d, template_vars) for var, var_d in to_resolve.get('variables', {}).items()}

        # Finished when there's nothing left to resolve or if to_resolve dict hasn't changed
        if to_resolve == resolved or \
            resolved['global']=={} and \
            all([var=={} for var in resolved['variables'].values()]):
            break

        to_resolve = resolved

        # Update with the resolved strings
        if 'global' in metadict:
            metadict['global'] |= to_resolve['global']
        if 'variables' in metadict:
            for var, var_d in to_resolve['variables'].items():
                metadict['variables'][var] |= var_d
    else:
        raise ValueError(f"Unable to resolve all Jinja template values after {LIMIT} attempts.\n"
                         f"It's likely that there is a circular key dependancy in:\n{metadict}")

    return metadict

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
        # Only valid to use jinja templates on strings
        # Templates are now expanded earlier in resolve_template but we need to catch those still undefined
        if isinstance(value, str):
            try:
                value = Template(value, undefined=StrictUndefined).render(template_vars)
            except UndefinedError as e:
                warn(f"Skip setting attribute '{attribute}': {e}")
                return
            finally:
                if verbose: print(f"      + {attribute}: {value}")

        group.setncattr(attribute, value)

def find_and_add_meta(ncfiles, metadata, fnregexs, sort_attrs=False, verbose=False):
    """
    Add meta data from 1 or more yaml formatted files to one or more
    netCDF files
    """
    # Resolve as much as possible in the shared template
    metadict = resolve_template(metadata, {})

    if verbose: print("Processing netCDF files:")
    for fname in ncfiles:
        if verbose: print(f"  {fname}")

        # Match supplied regex against filename and add metadata
        template_vars = match_filename_regex(fname, fnregexs, verbose)        
        add_meta(fname, metadata, template_vars, sort_attrs=sort_attrs, verbose=verbose)
        
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
