import argparse
from urllib.parse import urlparse
import json
from json_ref_dict import materialize, RefDict
from jsonschema import validate
from netCDF4 import Dataset


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


def get_schema(schema_source):
    """
    Load a schema object from a URL (resolving json-schema refs) or from a
    single file.

    Returns the schema as a dictionary
    """

    def _is_url(s):
        try:
            result = urlparse(s)
            return all([result.scheme, result.netloc])
        except AttributeError:
            return False

    if _is_url(schema_source):
        return materialize(RefDict(schema_source))
    else:
        with open(schema_source, "r") as f:
            return json.load(f)


def validate_file(filepath, schema):
    metadata = get_metadata_from_file(filepath)

    # Validate with raise an ValidationError if f is non-compliant
    validate(metadata, schema)


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
    parser.add_argument("files", help="netCDF files to validate", nargs="*")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")

    return parser.parse_args()


def main():
    args = parse_args()

    schema = get_schema(args.schema)

    for f in args.files:
        if args.verbose:
            print(f"Validating {f}")

        validate_file(f, schema)


if __name__ == "__main__":
    main()
