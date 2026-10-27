"""Tests for uncertainty trait validation."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.specs.traits.uncertainty import Uncertainty, validate_dataset


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


def _ensemble_ds(
    members: list[int | float | str], units: str | None = "1"
) -> xr.Dataset:
    """Create a minimal ensemble dataset for uncertainty tests.

    Parameters
    ----------
    members : list[int | float | str]
        Member coordinate values.
    units : str | None, optional
        Value for the ``units`` attribute of ``member``; omitted when ``None``.

    Returns
    -------
    xr.Dataset
        Test dataset instance.
    """
    ds = xr.Dataset(coords={"member": ("member", members)})
    ds.coords["member"].attrs["standard_name"] = "realization"
    if units is not None:
        ds.coords["member"].attrs["units"] = units
    return ds


def test_uncertainty_deterministic_passes() -> None:
    """Deterministic profile passes on a dataset without uncertainty dims."""
    report, _ = validate_dataset(xr.Dataset(), trait=Uncertainty.DETERMINISTIC)
    assert not report.has_fails()


def test_uncertainty_deterministic_fails_with_member_dim() -> None:
    """Deterministic profile fails when the dataset has a member dimension."""
    report, _ = validate_dataset(
        _ensemble_ds([0, 1, 2]), trait=Uncertainty.DETERMINISTIC
    )
    assert report.has_fails()


def test_uncertainty_deterministic_fails_with_quantile_dim() -> None:
    """Deterministic profile fails when the dataset has a quantile dimension."""
    report, _ = validate_dataset(
        _quantile_ds([0.1, 0.5, 0.9]), trait=Uncertainty.DETERMINISTIC
    )
    assert report.has_fails()


def test_uncertainty_deterministic_allows_scalar_member() -> None:
    """Deterministic profile passes with a scalar member coordinate."""
    ds = xr.Dataset(coords={"member": 3})
    report, _ = validate_dataset(ds, trait=Uncertainty.DETERMINISTIC)
    assert not report.has_fails()


def test_uncertainty_ensemble_passes() -> None:
    """Ensemble profile passes with integer, unique, attributed members."""
    report, _ = validate_dataset(_ensemble_ds([0, 1, 2]), trait=Uncertainty.ENSEMBLE)
    assert not report.has_fails()


def test_uncertainty_ensemble_fails_on_duplicate_members() -> None:
    """Ensemble profile fails when member values are not unique."""
    report, _ = validate_dataset(_ensemble_ds([0, 1, 1]), trait=Uncertainty.ENSEMBLE)
    assert report.has_fails()


def test_uncertainty_ensemble_fails_on_scalar_member() -> None:
    """Ensemble profile fails when member is a scalar coordinate."""
    ds = xr.Dataset(coords={"member": 3})
    report, _ = validate_dataset(ds, trait=Uncertainty.ENSEMBLE)
    assert report.has_fails()


def test_uncertainty_ensemble_fails_on_string_members() -> None:
    """Ensemble profile fails on string member labels."""
    report, _ = validate_dataset(
        _ensemble_ds(["0", "1", "2"]), trait=Uncertainty.ENSEMBLE
    )
    assert report.has_fails()


def test_uncertainty_ensemble_fails_on_float_members() -> None:
    """Ensemble profile fails on floating-point member values."""
    report, _ = validate_dataset(
        _ensemble_ds([0.0, 1.0, 2.0]), trait=Uncertainty.ENSEMBLE
    )
    assert report.has_fails()


def test_uncertainty_ensemble_passes_with_leading_member() -> None:
    """Ensemble profile passes when member is the first dim of each variable."""
    ds = _ensemble_ds([0, 1, 2])
    ds["t2m"] = (("member", "valid_time"), [[0.0, 0.0]] * 3)
    report, _ = validate_dataset(ds, trait=Uncertainty.ENSEMBLE)
    assert not report.has_fails()


def test_uncertainty_ensemble_fails_when_member_not_leading() -> None:
    """Ensemble profile fails when member is not the first dim of a variable."""
    ds = _ensemble_ds([0, 1, 2])
    ds["t2m"] = (("valid_time", "member"), [[0.0, 0.0, 0.0]] * 2)
    report, _ = validate_dataset(ds, trait=Uncertainty.ENSEMBLE)
    assert report.has_fails()


def test_uncertainty_ensemble_fails_without_units() -> None:
    """Ensemble profile fails when member has no units."""
    report, _ = validate_dataset(
        _ensemble_ds([0, 1, 2], units=None), trait=Uncertainty.ENSEMBLE
    )
    assert report.has_fails()


def test_uncertainty_quantile_passes() -> None:
    """Quantile profile passes when values and metadata are valid."""
    report, _ = validate_dataset(
        _quantile_ds([0.1, 0.5, 0.9]), trait=Uncertainty.QUANTILE
    )
    assert not report.has_fails()


def test_uncertainty_quantile_passes_without_standard_name() -> None:
    """Quantile profile does not require a standard_name (none exists in CF)."""
    ds = _quantile_ds([0.1, 0.5, 0.9], with_attrs=False)
    ds.coords["quantile"].attrs["units"] = "1"
    report, _ = validate_dataset(ds, trait=Uncertainty.QUANTILE)
    assert not report.has_fails()


def test_uncertainty_quantile_fails_when_quantile_not_leading() -> None:
    """Quantile profile fails when quantile is not the first dim of a variable."""
    ds = _quantile_ds([0.1, 0.5, 0.9])
    ds["t2m"] = (("valid_time", "quantile"), [[0.0, 0.0, 0.0]] * 2)
    report, _ = validate_dataset(ds, trait=Uncertainty.QUANTILE)
    assert report.has_fails()


def test_uncertainty_quantile_fails_out_of_bounds() -> None:
    """Quantile profile fails when any quantile value is outside [0, 1]."""
    report, _ = validate_dataset(
        _quantile_ds([-0.1, 0.5, 1.1]), trait=Uncertainty.QUANTILE
    )
    assert report.has_fails()
