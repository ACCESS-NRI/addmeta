#!/usr/bin/env python

"""
Copyright 2025 ACCESS-NRI

author: Joshua Torrance <joshua.torrance@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License"),
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import numpy as np
import pytest
import jsonschema
import referencing

from addmeta.validate import get_metadata_from_file, get_schema_validator, validate_file

from common import make_nc


ACCESS_OUTPUT_SCHEMA_URL = "https://raw.githubusercontent.com/ACCESS-NRI/schema/refs/heads/main/au.org.access-nri/model/output/file-metadata/2-0-0/2-0-0.json"


def test_get_metadata_from_file(make_nc):
    file = make_nc

    expected_metadata = {
        "global": {
            "unlikelytobeoverwritten": "total rubbish",
            "Publisher": "Will be overwritten",
        },
        "variables": {
            "Times": {
                "standard_name": "time",
                "units": "days since 2040-01-01 12:00:00",
                "calendar": "standard",
            },
            "temp": {
                "units": "degC",
                "_FillValue": np.float32(1.0e20),
                "missing_value": np.float32(1.0e20),
                "long_name": "Temperature",
            },
        },
    }
    metadata = get_metadata_from_file(file)

    assert metadata == expected_metadata


@pytest.mark.parametrize(
    "schema_source",
    [
        ACCESS_OUTPUT_SCHEMA_URL,
        "test/examples/schema/test_schema.json",
    ],
)
def test_get_schema(schema_source):
    schema = get_schema_validator(schema_source)

    # get_schema_validator should run without exception and return a non-empty dict
    assert schema


@pytest.mark.parametrize(
    "schema_source,expected_exception",
    [
        ("test/examples/schema/test_schema.json", None),
        ("test/examples/schema/contact.json", jsonschema.exceptions.ValidationError),
        (ACCESS_OUTPUT_SCHEMA_URL, jsonschema.exceptions.ValidationError),
        ("not_a_real_file.json", referencing.exceptions.Unresolvable),
        ("https://not_a_real_url.com/not_a_real_file.json", referencing.exceptions.Unresolvable),
    ],
)
def test_validate_file(schema_source, make_nc, expected_exception):
    file = make_nc
    schema = get_schema_validator(schema_source)

    if not expected_exception:
        # Validate should pass without exception
        validate_file(file, schema)
    else:
        with pytest.raises(expected_exception=expected_exception):
            validate_file(file, schema)
