import argparse
from urllib.parse import urlparse
import requests
import json
from jsonschema import Draft202012Validator
from netCDF4 import Dataset
from pathlib import Path
from referencing import Registry, Resource


def get_metadata_from_file(filepath):
    """
    Get the global and variable attributes from a netcdf file and return them
    as a nested dictionary.
    """
    d = {"global": {}, "variables": {}}

    def _get_nc_attrs(nc_group):
        return {attr: nc_group.getncattr(attr) for attr in nc_group.ncattrs()}

    with Dataset(filepath, "r") as ds:
        d["global"] = _get_nc_attrs(ds)

        for v in ds.variables.keys():
            d["variables"][v] = _get_nc_attrs(ds[v])

    return d


def is_url(s):
    try:
        result = urlparse(s)
        return result.scheme != '' and result.netloc != ''
    except AttributeError:
        return False


def retrieve_from_filesystem_or_httpx(path_or_url):
    if is_url(path_or_url):
        response = requests.get(path_or_url)
        contents = response.json()
    else:
        path = Path(path_or_url)
        contents = json.loads(path.read_text())

    return Resource.from_contents(contents)


def get_schema_validator(schema_source):
    """
    Load a schema object from a URL (resolving json-schema refs) or from a
    single file.

    Returns the Validator for the schema
    """
    # Build the registry to resolve the refs
    registry = Registry(retrieve=retrieve_from_filesystem_or_httpx)

    return Draft202012Validator({"$ref": schema_source}, registry=registry)


def validate_file(filepath, schema_validator):
    # Validate will raise an ValidationError if filepath is non-compliant
    schema_validator.validate(get_metadata_from_file(filepath))


def parse_args():
    parser = argparse.ArgumentParser(
        prog="validate",
        description="Validates a list of netCDF files against a json-schema. "
        "Will fail as soon as a non-compliant file is found.",
    )

    parser.add_argument(
        "-s",
        "--schema",
        nargs="?",
        required=True,
        help="The URL or file path of the schema to validate against.",
    )
    parser.add_argument("files", help="netCDF files to validate", nargs="+")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")

    return parser.parse_args()


def main():
    args = parse_args()

    schema_validator = get_schema_validator(args.schema)

    for f in args.files:
        if args.verbose:
            print(f"Validating {f}")

        validate_file(f, schema_validator)


if __name__ == "__main__":
    main()
