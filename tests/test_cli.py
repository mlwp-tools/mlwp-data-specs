"""Tests for trait CLI behavior."""

from __future__ import annotations

import xarray as xr
from pytest import CaptureFixture, MonkeyPatch

from mlwp_data_specs.specs import cli


def _forecast_grid_ds() -> xr.Dataset:
    """Create a minimal forecast + grid dataset for CLI tests.

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


def test_cli_requires_trait_selector() -> None:
    """CLI exits with parser error when no trait selector is provided."""
    try:
        cli.main(["some.zarr"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("Expected parser error")


def test_cli_runs_selected_traits(monkeypatch: MonkeyPatch) -> None:
    """CLI runs only selected trait validators and returns success on pass."""
    monkeypatch.setattr(xr, "open_zarr", lambda *args, **kwargs: _forecast_grid_ds())
    code = cli.main(["dummy.zarr", "--space", "grid", "--time", "forecast"])
    assert code == 0


def test_cli_print_spec_markdown(capsys: CaptureFixture[str]) -> None:
    """CLI prints markdown spec text when `--print-spec-markdown` is set."""
    code = cli.main(["--space", "grid", "--print-spec-markdown"])
    assert code == 0
    captured = capsys.readouterr()
    assert "trait: spatial_coordinate" in captured.out
