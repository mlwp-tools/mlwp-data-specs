"""Tests for uncertainty trait validation."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.specs.traits.uncertainty import validate_dataset
from mlwp_data_specs.traits.properties import Uncertainty


def _quantile_ds(values: list[float], with_attrs: bool = True) -> xr.Dataset:
    """Create a minimal quantile dataset for uncertainty tests.

    Parameters
    ----------
    values : list[float]
        Quantile coordinate values.
    with_attrs : bool, optional
        Whether to include required quantile metadata.

    Returns
    -------
    xr.Dataset
        Test dataset instance.
    """
    ds = xr.Dataset(coords={"quantile": ("quantile", values)})
    if with_attrs:
        ds.coords["quantile"].attrs.update({"standard_name": "quantile", "units": "1"})
    return ds


def test_uncertainty_quantile_passes() -> None:
    """Quantile profile passes when values and metadata are valid."""
    report, _ = validate_dataset(
        _quantile_ds([0.1, 0.5, 0.9]), trait=Uncertainty.QUANTILE
    )
    assert not report.has_fails()


def test_uncertainty_quantile_fails_out_of_bounds() -> None:
    """Quantile profile fails when any quantile value is outside [0, 1]."""
    report, _ = validate_dataset(
        _quantile_ds([-0.1, 0.5, 1.1]), trait=Uncertainty.QUANTILE
    )
    assert report.has_fails()
