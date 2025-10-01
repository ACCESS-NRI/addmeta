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

import os, sys
import argparse
import addmeta

def parse_args(args):
    """
    Parse arguments given as list (args)
    """

    parser = argparse.ArgumentParser(description="Add meta data to one or more netCDF files")

    parser.add_argument("-m","--metafiles", help="One or more meta-data files in YAML format", action='append')
    parser.add_argument("-l","--metalist", help="File containing a list of meta-data files", action='append')
    parser.add_argument("-f","--fn-regex", help="Extract metadata from filename using regex", action='append')
    parser.add_argument("-v","--verbose", help="Verbose output", action='store_true')
    parser.add_argument("files", help="netCDF files", nargs='+')

    return parser.parse_args(args)

def main(args):
    """
    Main routine. Takes return value from parse.parse_args as input
    """
    metafiles = []
    verbose = args.verbose

    if (args.metalist is not None):
        for listfile in args.metalist:
            metafiles.extend(addmeta.list_from_file(listfile))

    if (args.metafiles is not None):
        metafiles.extend(args.metafiles)

    if verbose: print("metafiles: "," ".join([str(f) for f in metafiles]))

    addmeta.find_and_add_meta(args.files, combine_meta(metafiles), args.fnregex)

def main_parse_args(args):
    """
    Call main with list of arguments. Callable from tests
    """
    # Must return so that check command return value is passed back to calling routine
    # otherwise py.test will fail
    return main(parse_args(args))

def main_argv():
    """
    Call main and pass command line arguments. This is required for setup.py entry_points
    """
    main_parse_args(sys.argv[1:])

if __name__ == "__main__":

    main_argv()
