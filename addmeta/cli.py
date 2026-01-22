#!/usr/bin/env python3

"""
Copyright 2019 ARC Centre of Excellence for Climate Extremes

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

import argparse
from datetime import datetime, timezone
from glob import glob
import os
from pathlib import Path
from platform import python_version
import sys

from addmeta import (
    find_and_add_meta,
    combine_meta,
    list_from_file,
    skip_comments,
    load_data_files,
    __version__ as addmeta_version,
)


def parse_args(args):
    """
    Parse arguments given as list (args)
    """

    parser = argparse.ArgumentParser(description="Add meta data to one or more netCDF files")

    parser.add_argument("-c","--cmdlineargs", help="File containing a list of command-line arguments", action='store')
    parser.add_argument("-m","--metafiles", help="One or more meta-data files in YAML format", action='append')
    parser.add_argument("-l","--metalist", help="File containing a list of meta-data files", action='append')
    parser.add_argument("-d","--datafiles", help="One or more key/value data files in YAML format", action='append')
    parser.add_argument("-f","--fnregex", help="Extract metadata from filename using regex", default=[], action='append')
    parser.add_argument("--datavar", help="Key/value pair to be added as data variable, e.g. --datavar 'var=value'", default=[], action='append')
    parser.add_argument("-s","--sort", help="Sort all keys lexicographically, ignoring case", action="store_true")
    parser.add_argument("--update-history", help="Update (or create) the history global attribute", action="store_true")
    parser.add_argument("-v","--verbose", help="Verbose output", action='store_true')
    parser.add_argument("files", help="netCDF files", nargs='*')

    return (parser, parser.parse_args(args))

def parse_key_value_pairs(pairs):
    """
    Parse a list of key=value strings into a dictionary
    """
    result = {}
    for pair in pairs:
        if '=' not in pair:
            raise ValueError(f"Invalid key/value pair: {pair}. Expected format: key=value")
        key, value = pair.split('=', 1)
        result[key] = value
    return result

def main(args):
    """
    Main routine. Takes return value from parse.parse_args as input
    """
    metafiles = []
    verbose = args.verbose
    kwdata = {}

    if (args.datafiles is not None):
        if verbose: print("datafiles: "," ".join([str(f) for f in args.datafiles]))
        kwdata = load_data_files(args.datafiles)

    # Process keyword --datavar command line arguments
    if args.datavar:
        if verbose: print("datavar: "," ".join([str(v) for v in args.datavar]))
        try:
            datavar_dict = parse_key_value_pairs(args.datavar)
            # Add to kwdata under 'datavar' namespace
            kwdata['__argdata__'] = datavar_dict
        except ValueError as e:
            if verbose: print(f"Error parsing datavar: {e}")
            raise

    if (args.metalist is not None):
        for line in args.metalist:
            metafiles.extend(list_from_file(line))

    if (args.metafiles is not None):
        metafiles.extend(args.metafiles)

    if verbose: print("metafiles: "," ".join([str(f) for f in metafiles]))
    
    if args.update_history:
        history = build_history(args.files)
    else:
        history = None

    find_and_add_meta(
        args.files,
        combine_meta(metafiles),
        kwdata,
        args.fnregex,
        sort_attrs=args.sort,
        history=history,
        verbose=verbose,
    )

def safe_join_lists(list1, list2):
    """
    Joins two lists, handling cases where one or both might be None.
    Returns:
        A new list containing the combined elements, or None if both are None.
    """
    if list1 is None and list2 is None:
        return None
    elif list1 is None:
        return list2
    elif list2 is None:
        return list1
    else:
        return list1 + list2

def resolve_relative_paths(files, base_path):
    """
    Resolve relative paths for a list of files against a base path.
    """
    resolved = []
    for file in files:
        file = os.path.expandvars(file)
        if os.path.isabs(file):
            resolved.extend(glob(file))
        else:
            resolved.extend([str(f) for f in base_path.glob(file)])
    return resolved

def build_history(files):
    time_stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    python_exe = f"python{python_version()}"

    # The list of files given on the commandline is not needed in the history
    args = " ".join([a for a in sys.argv if a not in files])
  
    return f"{time_stamp} : addmeta {addmeta_version} : {python_exe} {args}"

def main_parse_args(args):
    """
    Call main with list of arguments. Callable from tests
    """

    parser, parsed_args = parse_args(args)

    if (parsed_args.cmdlineargs is not None):
        # If a cmdlineargs file has been specified, read every line 
        # and parse
        cmdlinefile = Path(parsed_args.cmdlineargs)
        try:
            with open(cmdlinefile, 'r') as file:
                newargs = [line for line in skip_comments(file)]
        except FileNotFoundError:
            sys.exit(f"Error: cmdlineargs file '{cmdlinefile}' not found")
        else:
            _, new_parsed_args = parse_args(newargs)

        # Convert relative paths in metafiles to be relative to cmdlineargs file
        if new_parsed_args.metafiles is not None:
            new_parsed_args.metafiles = resolve_relative_paths(new_parsed_args.metafiles, cmdlinefile.parent)

        # Convert relative paths in datafiles to be relative to cmdlineargs file
        if new_parsed_args.datafiles is not None:
            new_parsed_args.datafiles = resolve_relative_paths(new_parsed_args.datafiles, cmdlinefile.parent)

        # Expand (glob) patterns in positional arguments (files) and convert relative paths
        if new_parsed_args.files is not None:
            new_parsed_args.files = resolve_relative_paths(new_parsed_args.files, cmdlinefile.parent)

        # Combine new and existing parsed arguments, ommitting cmdlineargs 
        # option.  Adding additional command line arguments may require 
        # adding logic here also
        parsed_args.files = safe_join_lists(parsed_args.files, new_parsed_args.files)
        parsed_args.metafiles = safe_join_lists(parsed_args.metafiles, new_parsed_args.metafiles)
        parsed_args.datafiles = safe_join_lists(parsed_args.datafiles, new_parsed_args.datafiles)
        parsed_args.fnregex = safe_join_lists(parsed_args.fnregex, new_parsed_args.fnregex)
        parsed_args.datavar = safe_join_lists(parsed_args.datavar, new_parsed_args.datavar)
        parsed_args.verbose = parsed_args.verbose or new_parsed_args.verbose
        parsed_args.cmdlineargs = None


    # Have to manually check positional arguments
    if len(parsed_args.files) < 1:
        parser.print_usage()
        sys.exit('Error: no files specified')
    
    # Must return so that check command return value is passed back to calling routine
    # otherwise py.test will fail
    return parsed_args

def main_argv():
    """
    Call main and pass command line arguments. This is required for setup.py entry_points
    """
    main(main_parse_args(sys.argv[1:]))

if __name__ == "__main__":

    main_argv()
