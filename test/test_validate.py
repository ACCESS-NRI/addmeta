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

from addmeta.validate import get_metadata_from_file, get_schema, validate_file

from common import make_nc


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
        "https://raw.githubusercontent.com/ACCESS-NRI/schema/refs/heads/main/au.org.access-nri/model/output/file-metadata/2-0-0/2-0-0.json",
        "test/examples/schema/test_schema.json",
    ],
)
def test_get_schema_from_url(schema_source):
    schema = get_schema(schema_source)

    # get_schema should run without exception and return a non-empty dict
    assert schema


@pytest.mark.parametrize(
    "schema_source,is_valid",
    [
        ("test/examples/schema/test_schema.json", True),
        ("test/examples/schema/contact.json", False),
    ],
)
def test_validate_file(schema_source, make_nc, is_valid):
    file = make_nc
    schema = get_schema(schema_source)

    if is_valid:
        validate_file(file, schema)
    else:
        with pytest.raises(jsonschema.exceptions.ValidationError):
            validate_file(file, schema)
