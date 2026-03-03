"""Tests for time trait validation."""

from __future__ import annotations

import numpy as np
import xarray as xr

from mlwp_data_specs.traits.properties import Time
from mlwp_data_specs.traits.time_coordinate import validate_dataset


def _observation_ds(valid: bool = True) -> xr.Dataset:
    """Create a minimal observation-style dataset for time trait tests.

    Parameters
    ----------
    valid : bool, optional
        Whether to include required `standard_name` metadata.

    Returns
    -------
    xr.Dataset
        Test dataset instance.
    """
    ds = xr.Dataset(
        coords={"valid_time": ("valid_time", np.array(["2026-01-01T00:00:00"], dtype="datetime64[ns]"))}
    )
    if valid:
        ds.coords["valid_time"].attrs["standard_name"] = "time"
    return ds


def test_time_observation_passes() -> None:
    """Observation profile passes when valid_time metadata is compliant."""
    report, _ = validate_dataset(_observation_ds(valid=True), trait=Time.OBSERVATION)
    assert not report.has_fails()


def test_time_observation_fails_without_standard_name() -> None:
    """Observation profile fails when valid_time lacks `standard_name`."""
    report, _ = validate_dataset(_observation_ds(valid=False), trait=Time.OBSERVATION)
    assert report.has_fails()
