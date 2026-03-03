"""Tests for public Python API entry points."""

from __future__ import annotations

import pytest
import xarray as xr

from mlwp_data_specs import check_dataset


def _forecast_grid_ds() -> xr.Dataset:
    """Create a forecast + grid dataset that satisfies selected checks.

    Returns
    -------
    xr.Dataset
        Test dataset instance.
    """
    ds = xr.Dataset(
        coords={
            "reference_time": ("reference_time", [0]),
            "lead_time": ("lead_time", [1]),
            "longitude": ("longitude", [10.0, 11.0]),
            "latitude": ("latitude", [60.0, 61.0]),
        }
    )
    ds.coords["reference_time"].attrs["standard_name"] = "forecast_reference_time"
    ds.coords["lead_time"].attrs.update(
        {"standard_name": "forecast_period", "units": "hours"}
    )
    ds.coords["longitude"].attrs.update(
        {"standard_name": "longitude", "units": "degrees_east"}
    )
    ds.coords["latitude"].attrs.update(
        {"standard_name": "latitude", "units": "degrees_north"}
    )
    return ds


def test_check_dataset_accepts_string_traits() -> None:
    """API accepts string trait selectors and returns a passing report."""
    report = check_dataset(_forecast_grid_ds(), time="forecast", space="grid")
    assert not report.has_fails()


def test_check_dataset_supports_uncertaity_alias() -> None:
    """API accepts the spelled-as-requested uncertainty alias argument."""
    report = check_dataset(
        _forecast_grid_ds(), time="forecast", space="grid", uncertaity="deterministic"
    )
    assert not report.has_fails()


def test_check_dataset_requires_trait() -> None:
    """API raises when no traits are selected."""
    with pytest.raises(ValueError, match="At least one trait"):
        check_dataset(_forecast_grid_ds())
