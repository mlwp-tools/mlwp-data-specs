"""Tests for public Python API entry points."""

from __future__ import annotations

import pytest
import xarray as xr

from mlwp_data_specs import import_loader_hooks, open_dataset, validate_dataset


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


def test_validate_dataset_accepts_string_traits() -> None:
    """API accepts string trait selectors and returns a passing report."""
    report = validate_dataset(_forecast_grid_ds(), time="forecast", space="grid")
    assert not report.has_fails()


def test_validate_dataset_supports_uncertaity_alias() -> None:
    """API accepts the spelled-as-requested uncertainty alias argument."""
    report = validate_dataset(
        _forecast_grid_ds(), time="forecast", space="grid", uncertaity="deterministic"
    )
    assert not report.has_fails()


def test_validate_dataset_requires_trait() -> None:
    """API raises when no traits are selected."""
    with pytest.raises(ValueError, match="At least one trait"):
        validate_dataset(_forecast_grid_ds())


def test_import_loader_hooks_defaults_from_module(tmp_path) -> None:
    """Loader modules may omit hooks and fall back to built-in defaults."""
    loader_file = tmp_path / "loader_defaults.py"
    loader_file.write_text("", encoding="utf-8")

    hooks = import_loader_hooks(str(loader_file))

    assert hooks == {}


def test_open_dataset_uses_loader_hooks(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """API opens datasets through the configured loader module when requested."""
    loader_file = tmp_path / "loader_hooks.py"
    loader_file.write_text(
        "\n".join(
            [
                "CONCAT_DIM = 'sample'",
                "def preprocess(ds):",
                "    return ds.rename({'reference_time': 'sample'})",
                "def postprocess(ds):",
                "    return ds.assign_coords(source=('sample', ['loader']))",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())

    ds = open_dataset("dummy.zarr", loader=str(loader_file))

    assert "sample" in ds.dims
    assert ds.coords["source"].item() == "loader"


def test_import_loader_hooks_builtin_anemoi_module() -> None:
    """Built-in loader modules are importable through the public hook API."""
    hooks = import_loader_hooks("mlwp_data_specs.loaders.anemoi.anemoi_datasets")

    assert hooks["open_kwargs"] == {"engine": "zarr", "consolidated": False}
    assert callable(hooks["preprocess"])
    assert hooks["concat_dim"] == "valid_time"
    assert callable(hooks["postprocess"])
    assert "valid_time_profiles" not in hooks


def test_open_dataset_rejects_incompatible_loader_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API rejects trait selections that the loader declares as incompatible."""
    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())

    with pytest.raises(ValueError, match="Loader does not support time='observation'"):
        open_dataset(
            ["a.nc", "b.nc"],
            loader="mlwp_data_specs.loaders.anemoi.anemoi_inference",
            time="observation",
        )


def test_open_dataset_requires_concat_dim_for_multiple_inputs(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """API raises when multiple inputs are provided without a concat dimension."""
    loader_file = tmp_path / "loader_without_concat.py"
    loader_file.write_text("", encoding="utf-8")

    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())

    with pytest.raises(ValueError, match="Loader must define 'concat_dim'"):
        open_dataset(
            ["a.nc", "b.nc"],
            loader=str(loader_file),
            time="forecast",
        )
