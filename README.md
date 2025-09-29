[![Build Status](https://travis-ci.org/coecms/addmeta.svg?branch=master)](https://travis-ci.org/coecms/addmeta)
[![codecov.io](https://codecov.io/github/coecms/addmeta/coverage.svg?branch=master)](https://codecov.io/github/coecms/addmeta?branch=master)

# addmeta

Add meta data to netCDF files.

## Metadata

The metadata is stored in attribute files in [YAML](https://yaml.org) format. 
The metadata is in key-value pairs and is a global attribute if defined in a 
`global` section, or applied to a specific named variable in the `variables` 
section. 

If an attribute is listed with a missing value that attribute is deleted from the file.

For example the following is an example of an attribute file:
```yaml
global:
    # Mandatory since it gives a key to all the other attributes
    Conventions: "CF-1.7, ACDD-1.3"
    # The url of the license applied to the data
    license: "http://creativecommons.org/licenses/by-nc-sa/4.0/"
variables:
    yt_ocean:
        _FillValue:
        long_name: "latitude in rotated pole grid"
        units: "degrees"
    geolat_t:
        long_name: "latitude coordinate"
        units: "degrees_north"
        standard_name: "latitude"
```
It will create (or replace) two global attributes: `Conventions` and `license`.
It will also create (or replace) attributes for two variables, `yt_ocean` and
`geolat_t`, and delete the `_FillValue` attribute of `yt_ocean`.

The information is read into a `python` dict. Multiple attribute files can be
specified. If the same attribute is defined more than once, the last attribute
file specified takes precedence. Like cascading style sheets this means default
values can be given and overridden when necessary. 

### metadata.yaml support

ACCESS-NRI models produce, and intake catalogues consume, a `metadata.yaml` file
that is a series of key/value pairs (see 
[schema](https://github.com/ACCESS-NRI/schema/tree/main/au.org.access-nri/model/output/experiment-metadata) 
for details).

Simple key/value pairs are supported by `addmeta` and are assumed to define global
metadata.


## Invocation

`addmeta` is a command line program. Invoking with the `-h` flag prints
a summay of how to invoke the program correctly.

    $ addmeta -h
    usage: addmeta [-h] [-m METAFILES] [-l METALIST] [-v] files [files ...]

    Add meta data to one or more netCDF files

    positional arguments:
    files                 netCDF files

    optional arguments:
    -h, --help            show this help message and exit
    -m METAFILES, --metafiles METAFILES
                            One or more meta-data files in YAML format
    -l METALIST, --metalist METALIST
                            File containing a list of meta-data files
    -v, --verbose         Verbose output

Multiple attribute files can be specified by passing more than one file with
the `-m` option. For a large number of files this can be tedious. In that case
use the `-l` option and pass it a text file with the names of attribute files,
one per line.

Multiple meta list files and meta files can be specified on one command line.

