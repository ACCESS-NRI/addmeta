import netCDF4 as nc
import pytest

from addmeta import add_meta
from addmeta.addmeta import _referenced_variables
from common import make_nc


def get_attributes(filename, variable):
    with nc.Dataset(filename) as dataset:
        return dict(dataset.variables[variable].__dict__)


@pytest.mark.parametrize(
    ("attribute", "value", "expected"),
    [
        ("coordinates", "lat lon", ["lat", "lon"]),
        ("ancillary_variables", "a b c", ["a", "b", "c"]),
        ("bounds", "missing_bounds", ["missing_bounds"]),
        ("cell_measures", "area: area volume: volume", ["area", "volume"]),
        ("formula_terms", "a: temp b: lon", ["temp", "lon"]),
        (
            "cell_methods",
            "Times: mean (interval: 1 hour comment: sampled instantaneously) temp: salt: maximum",
            ["Times", "temp", "salt"],
        ),
    ],
)
def test_referenced_variables(attribute, value, expected):
    assert _referenced_variables(attribute, value) == expected


def test_missing_reference_is_skipped(make_nc):
    metadata = {"variables": {"temp": {"bounds": "missing_bounds"}}}

    with pytest.warns(UserWarning, match="missing_bounds"):
        add_meta(make_nc, metadata, {}, cf_compliance=True)

    assert "bounds" not in get_attributes(make_nc, "temp")


def test_existing_and_external_references_are_written(make_nc):
    metadata = {
        "global": {
            "external_variables": "external_bounds external_area external_a"
        },
        "variables": {
            "temp": {
                "coordinates": "Times",
                "bounds": "external_bounds",
                "cell_measures": "area: external_area",
                "formula_terms": "a: external_a b: Times",
                "cell_methods": "Times: mean",
            }
        },
    }

    add_meta(make_nc, metadata, {}, cf_compliance=True)
    attributes = get_attributes(make_nc, "temp")

    assert attributes["coordinates"] == "Times"
    assert attributes["bounds"] == "external_bounds"
    assert attributes["cell_measures"] == "area: external_area"
    assert attributes["formula_terms"] == "a: external_a b: Times"
    assert attributes["cell_methods"] == "Times: mean"


@pytest.mark.parametrize("cf_compliance", [False, True])
def test_complicated_cell_methods_are_checked(make_nc, cf_compliance):
    cell_methods = "temp: salt: maximum"
    metadata = {"variables": {"temp": {"cell_methods": cell_methods}}}

    add_meta(make_nc, metadata, {}, cf_compliance=cf_compliance, verbose=True)

    attributes = get_attributes(make_nc, "temp")
    if cf_compliance:
        assert "cell_methods" not in attributes
    else:
        assert attributes["cell_methods"] == cell_methods


def test_missing_cell_methods_reference_is_skipped(make_nc):
    cell_methods = "Times: mean (interval: 1 hour) missing: maximum"
    metadata = {"variables": {"temp": {"cell_methods": cell_methods}}}

    with pytest.warns(UserWarning, match="missing"):
        add_meta(make_nc, metadata, {}, cf_compliance=True)

    assert "cell_methods" not in get_attributes(make_nc, "temp")


def test_templated_reference_is_checked_after_rendering(make_nc):
    metadata = {"variables": {"temp": {"coordinates": "{{ coordinate }}"}}}

    add_meta(make_nc, metadata, {"coordinate": "Times"}, cf_compliance=True)

    assert get_attributes(make_nc, "temp")["coordinates"] == "Times"
