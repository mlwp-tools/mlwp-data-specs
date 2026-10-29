"""Tests for global attribute checks."""

from __future__ import annotations

import pytest
import xarray as xr

from mlwp_data_specs.checks.global_attributes.traits import check_trait_attribute
from mlwp_data_specs.specs.traits.time_coordinate import TIME_TRAIT_ATTR
from mlwp_data_specs.trait_profiles import Time


@pytest.mark.parametrize(
    ("attrs", "expected_status"),
    [
        ({}, "PASS"),
        ({TIME_TRAIT_ATTR: Time.FORECAST}, "PASS"),
        ({TIME_TRAIT_ATTR: Time.OBSERVATION}, "WARNING"),
        ({TIME_TRAIT_ATTR: "nowcast"}, "FAIL"),
    ],
)
def test_check_trait_attribute(attrs: dict[str, str], expected_status: str) -> None:
    """Absent or matching attributes pass, mismatches warn, invalid values fail.

    Parameters
    ----------
    attrs : dict[str, str]
        Global attributes of the test dataset.
    expected_status : str
        Expected status of the single reported result.
    """
    ds = xr.Dataset(attrs=attrs)
    report = check_trait_attribute(
        ds, trait_axis="time", trait_cls=Time, trait=Time.FORECAST
    )

    assert [r.status for r in report.results] == [expected_status]
    assert report.results[0].section == "Time Coordinate"


@pytest.mark.parametrize(
    ("attrs", "expected_status"),
    [
        ({TIME_TRAIT_ATTR: Time.OBSERVATION}, "PASS"),
        ({TIME_TRAIT_ATTR: "nowcast"}, "FAIL"),
    ],
)
def test_check_trait_attribute_without_trait(
    attrs: dict[str, str], expected_status: str
) -> None:
    """Without a validated profile, only the validity of the value is checked.

    Parameters
    ----------
    attrs : dict[str, str]
        Global attributes of the test dataset.
    expected_status : str
        Expected status of the single reported result.
    """
    ds = xr.Dataset(attrs=attrs)
    report = check_trait_attribute(ds, trait_axis="time", trait_cls=Time)

    assert [r.status for r in report.results] == [expected_status]
