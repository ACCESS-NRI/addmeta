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

### Dynamic templating

`addmeta` supports limited dynamic templating to allow injection of file specific
metadata in a general way. This is done using 
[Jinja templating](https://jinja.palletsprojects.com/en/stable/) and template variables.

Template variables are defined in four ways: automatically generated based on file
attributes, automatically generated but user-configured based on filename, statically
defined in user defined files, and via command line arguments.

#### File attributes

A number of file attributes variables are automatically provided in a pre-populated 
special namespaces: `__file__` and `__datetime__`:

|variable| description|
|----|----|
|`__file__.mtime`|Last modification time|
|`__file__.size`|File size (in bytes)|
|`__file__.parent`|Parent directory of the netCDF file|
|`__file__.name`|Filename of the netCDF file|
|`__file__.fullpath`|Full path of the netCDF file|
|`__datetime__.now`|The datetime addmeta is run|

These variables can be used in a metadata file like so:
```yaml
global:
    Publisher: "ACCESS-NRI"
    directory: "{{ __file__.parent }}"
    Year: 2025
    filename: "{{ __file__.name }}"
    size: "{{ __file__.size }}"
    modification_time: "{{ __file__.mtime }}"
    date_metadata_modified: "{{ __file__.now }}"
```

> [!CAUTION]
> Jinja template variables **must be quoted** and as a consequence all are saved
> as string attributes in the netCDF variable

#### Filename

Often important file level properties are encoded in filenames. This is not an optimal
solution, but comes about because it is not possible to alter the model code to inject
the metadata directly into the output files.

`addmeta` supports extracting this information and embedding it dynamically as an extension
to dynamic templating.

Extracting the variable is done by specifying [python regular expressions with named
groups](https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups), 
and the group names become the metadata template variables, accessible in the `__file__` 
namespace.  e.g.

For the filename
```bash
access-om3.mom6.3d.agessc.1day.mean.1900-01.nc'
```
the following regex:
```python
r'.*\.(?P<freq>.*)\.mean\.\d+-\d+\.nc$'
```
would match and set `freq=1day`.  This could then be referred to like so
```yaml
    frequency: {{ __file__.freq }}
```
It is possible to define more than one named
group in a regex, as long as the names are unique. It is also possible to specify multiple
regex expressions, only those that match will return variables that can be used as 
jinja template variables. Unused variables are ignored, and in the case of identical
named groups in different regexes, later defined regexes override previous ones.

#### User defined template variables

User defined template variables can be defined in two ways, in *datafiles* or directly
as command line arguments.  

##### Datafiles 

Yaml formatted *datafiles* are specified via `-d/--datafiles` command line argument. They
should be simple string key/value pairs. Values that are lists are converted to comma
separated (CSV) strings. The keys are accessible through a namespace defined as the 
[stem of the yaml filename](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.stem)
they are read from.

For example:

and `addmeta` invoked like so
```bash
addmeta -d job.yaml -m meta.yaml file.nc
```
and datafile `job.yaml`
```yaml
SHELL: '/bin/bash'
pbs_id: '1234567'
```
and metadata file `meta.yaml`
```yaml
global:
    license: 'CC-BY-4.0'
    shell: {{ job.SHELL }}
    id: {{ job.pbs_id }}
```
`file.nc` will have global metadata:
```
// global attributes:
		:license = "CC-BY-4.0" ;
		:id = "1234567";
		:shell = "/bin/bash";
```
This approach works particularly well when only a small subset of the data from 
the datafile is required to be inserted into the file metadata, or when the value
is required, but the key needs to be different.

Multiple datafiles can be specified, and the variables from each will be accessible
in a namespace defined by the 
[stem of the filename](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.stem).

#### Command line

Template variables can also be directly specified via the command line option `--datavar`
and can be accessed in the special namespace `__argdata__`. For example:

Using the example above with a modified metadata file `meta.yaml`
```yaml
global:
    license: 'CC-BY-4.0'
    shell: {{ job.SHELL }}
    id: {{ job.pbs_id }}
    frequency: {{ __argdata__.freq }}
```
and adding a single `--datavar freq='1daily'` option:
```bash
addmeta -d job.yaml -m meta.yaml --datavar freq='1daily' file.nc
```
`file.nc` will have global metadata
```
// global attributes:
		:license = "CC-BY-4.0" ;
		:id = "1234567";
		:shell = "/bin/bash";
		:frequency = "1daily";
```
Multiple variables can be defined in this way with multiple `--datavar` options.

### metadata.yaml support

ACCESS-NRI models produce, and intake catalogues consume, a `metadata.yaml` file
that is a series of key/value pairs (see 
[schema](https://github.com/ACCESS-NRI/schema/tree/main/au.org.access-nri/model/output/experiment-metadata) 
for details).

Simple key/value pairs are supported by `addmeta` and are assumed to define global
metadata.

This approach is best suited when most of the key/pairs of a `metadata.yaml` file
will be used. When only a small number of fields are required it is best to use
the user defined data templating approach described above.

### History

netCDF applications are expected to update the history attribute when modifying
the files. This can be enabled in `addmeta` with the `--update-history`
commandline argument.

## Invocation

`addmeta` provides a command line interface. Invoking with the `-h` flag prints
a summay of how to invoke the program correctly.

    $ addmeta -h
    usage: addmeta [-h] [-c CMDLINEARGS] [-m METAFILES] [-l METALIST] [-d DATAFILES] [-f FNREGEX] [-s] [-v] [files ...]

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
    -d DATAFILES, --datafiles DATAFILES
                            One or more key/value data files in YAML format
    -f FNREGEX, --fnregex FNREGEX
                            Extract metadata from filename using regex
    -s, --sort            Sort all keys lexicographically, ignoring case
    --update-history      Update or create the history global attribute
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
# Re-use experiment level metadata as template variables
-d=../metadata.yaml
# Ocean model specific global metadata
-m=meta_ocean_global.yaml
# Ocean model specific variable metadata
-m=meta_ocean_variable.yaml
# Extract frequency from filename 
--fn-regex=.*\.(?P<frequency>.*)\.mean\.\d+-\d+\.nc$
# Apply to all ocean data in $OUTPUTDIR directory (defined at runtime)
${OUTPUTDIR}/output/ocean_*.nc
```
The use of environment variables for files paths is supported, however
absolute paths are recommended as `addmeta` tries to resolve relative paths
relative to the location of the command file, which that could lead to errors.

> [!CAUTION]
> Do not quote regex strings in a command file as above. String quoting is still
> required when used on the command line.
>
> The python [argparse library](https://docs.python.org/3/library/argparse.html) 
> does not allow mixing of command line options and positional arguments. So
> all the references to netCDF files need to come at the end of the argument
> list. 

