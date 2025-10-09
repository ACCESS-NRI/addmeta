[![pytests](https://github.com/ACCESS-NRI/addmeta/actions/workflows/pytest.yml/badge.svg)](https://github.com/ACCESS-NRI/addmeta/actions/workflows/pytest.yml)
[![CD](https://github.com/ACCESS-NRI/addmeta/actions/workflows/CD.yml/badge.svg)](https://github.com/ACCESS-NRI/addmeta/actions/workflows/CD.yml)

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

### Dynamic templating

`addmeta` supports limited dynamic templating to allow injection of file specific
metadata in a general way. This is done using 
[Jinja templating](https://jinja.palletsprojects.com/en/stable/) and providing a
number of pre-populated variables:

|variable| description|
|----|----|
|`mtime`|Last modification time|
|`size`|File size (in bytes)|
|`parent`|Parent directory of the netCDF file|
|`name`|Filename of the netCDF file|
|`fullpath`|Full path of the netCDF file|

These variables can be used in a metadata file like so:

```yaml
global:
    Publisher: "ACCESS-NRI"
    directory: "{{ parent }}"
    Year: 2025
    filename: "{{ name }}"
    size: "{{ size }}"
    modification_time: "{{ mtime }}"
```

> [!CAUTION]
> Jinja template variables **must be quoted** and as a consequence all are saved
> as string attributes in the netCDF variable

### Filename based dynamic templating

Often important file level properties are encoded in filenames. This is not an optimal
solution, but comes about because it is not possible to alter the model code to inject
the metadata directly into the output files.

`addmeta` supports extracting this information and embedding it dynamically as an extension
to dynamic templating.

Extracting the variable is done by specifying [python regular expressions with named
groups](https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups), 
and the group names become the metadata template variables.  e.g.

For the filename
```bash
access-om3.mom6.3d.agessc.1day.mean.1900-01.nc'
```
the following regex:
```python
r'.*\.(?P<frequency>.*)\.mean\.\d+-\d+\.nc$'
```
would match and set `frequency=1day`. It is possible to define more than one named
group in a regex, as long as the names are unique. It is also possible to specify multiple
regex expressions, only those that match will return variables that can be used as 
jinja template variables. Unused variables are ignored, and in the case of identical
named groups in different regexs, later defined regexs override previous ones.

## Invocation

`addmeta` provides a command line interface. Invoking with the `-h` flag prints
a summay of how to invoke the program correctly.

    $ addmeta -h
    usage: cli.py [-h] [-c CMDLINEARGS] [-m METAFILES] [-l METALIST] [-f FN_REGEX] [-v] files [files ...]

    Add meta data to one or more netCDF files

    positional arguments:
    files                 netCDF files

    options:
    -h, --help            show this help message and exit
    -c CMDLINEARGS, --cmdlineargs CMDLINEARGS
                            File containing a list of command-line arguments
    -m METAFILES, --metafiles METAFILES
                            One or more meta-data files in YAML format
    -l METALIST, --metalist METALIST
                            File containing a list of meta-data files
    -f FN_REGEX, --fn-regex FN_REGEX
                            Extract metadata from filename using regex
    -v, --verbose         Verbose output


Multiple attribute files can be specified by passing more than one file with
the `-m` option. For a large number of files this can be tedious. In that case
use the `-l` option and pass it a text file with the names of attribute files,
one per line.

Multiple meta list files and meta files can be specified on one command line.

To support scriptable invocation command line arguments can be saved into a 
file and consumed with `-c <filename>`. A good practice is to have a command line
argument per line, to make it easy to read, and a `diff` of isolates the change.
Whitespace and comments are stripped, so it is also possible to add useful comments.
e.g.
```bash
# Re-use experiment level metadata
-m=../metadata.yaml
# Ocean model specific global metadata
-m=meta_ocean_global.yaml
# Ocean model specific variable metadata
-m=meta_ocean_variable.yaml
# Extract frequency from filename 
--fn-regex=.*\.(?P<frequency>.*)\.mean\.\d+-\d+\.nc$
# Apply to all ocean data in output subdirectory
output/ocean_*.nc
```

> [!CAUTION]
> Do not quote regex strings in a command file as above. String quoting is still
> required when used on the command line.
>
> The python [argparse library](https://docs.python.org/3/library/argparse.html) 
> does not allow mixing of command line options and positional arguments. So
> all the references to netCDF files need to come at the end of the argument
> list. 