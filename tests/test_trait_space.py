"""Tests for spatial trait validation."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.traits.properties import Space
from mlwp_data_specs.traits.spatial_coordinate import validate_dataset


def _grid_ds(with_metadata: bool = True) -> xr.Dataset:
    """Create a minimal grid-style dataset for spatial trait tests.

    Parameters
    ----------
    with_metadata : bool, optional
        Whether to attach required coordinate metadata.

    Returns
    -------
    xr.Dataset
        Test dataset instance.
    """
    ds = xr.Dataset(
        coords={
            "longitude": ("longitude", [10.0, 11.0]),
            "latitude": ("latitude", [60.0, 61.0]),
        }
    )
    if with_metadata:
        ds.coords["longitude"].attrs.update({"standard_name": "longitude", "units": "degrees_east"})
        ds.coords["latitude"].attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    return ds


def test_space_grid_passes_basic_requirements() -> None:
    """Grid profile passes with required dims/coords and metadata."""
    report, _ = validate_dataset(_grid_ds(), trait=Space.GRID)
    assert not report.has_fails()


def test_space_grid_fails_missing_standard_name() -> None:
    """Grid profile fails when required coordinate metadata is absent."""
    ds = _grid_ds(with_metadata=False)
    report, _ = validate_dataset(ds, trait=Space.GRID)
    assert report.has_fails()
