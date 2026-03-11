"""Tests for trait CLI behavior."""

from __future__ import annotations

from pathlib import Path

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
    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())
    code = cli.main(["dummy.zarr", "--space", "grid", "--time", "forecast"])
    assert code == 0


def test_cli_print_spec_markdown(capsys: CaptureFixture[str]) -> None:
    """CLI prints markdown spec text when `--print-spec-markdown` is set."""
    code = cli.main(["--space", "grid", "--print-spec-markdown"])
    assert code == 0
    captured = capsys.readouterr()
    assert "trait: spatial_coordinate" in captured.out


def test_cli_uses_loader_module(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """CLI opens datasets through a user-provided loader module."""
    loader_file = tmp_path / "loader_hooks.py"
    loader_file.write_text(
        "\n".join(
            [
                "def preprocess(ds):",
                "    return ds.assign_coords(loader_flag=1)",
                "def postprocess(ds):",
                "    return ds",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())

    def _validate(ds, *, space, time, uncertainty):
        assert ds.coords["loader_flag"].item() == 1
        return cli.ValidationReport(), []

    monkeypatch.setattr(cli, "_run_selected_validations", _validate)

    code = cli.main(
        [
            "dummy.zarr",
            "--loader",
            str(loader_file),
            "--space",
            "grid",
            "--time",
            "forecast",
        ]
    )

    assert code == 0


def test_cli_accepts_multiple_dataset_paths(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """CLI passes multiple dataset paths through to the loader-aware opener."""
    observed: dict[str, object] = {}

    def _open_dataset(dataset_path, **kwargs):
        observed["dataset_path"] = dataset_path
        return _forecast_grid_ds()

    monkeypatch.setattr(cli, "open_dataset", _open_dataset)

    def _validate(ds, *, space, time, uncertainty):
        return cli.ValidationReport(), []

    monkeypatch.setattr(cli, "_run_selected_validations", _validate)

    code = cli.main(
        [
            "a.nc",
            "b.nc",
            "--loader",
            "mlwp_data_specs.loaders.anemoi.anemoi_inference",
            "--space",
            "grid",
            "--time",
            "forecast",
        ]
    )

    assert code == 0
    assert observed["dataset_path"] == ["a.nc", "b.nc"]


def test_cli_rejects_incompatible_loader_profile(monkeypatch: MonkeyPatch) -> None:
    """CLI rejects trait selections unsupported by the chosen loader."""
    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())

    code = cli.main(
        [
            "a.nc",
            "b.nc",
            "--loader",
            "mlwp_data_specs.loaders.anemoi.anemoi_inference",
            "--space",
            "grid",
            "--time",
            "observation",
        ]
    )

    assert code is None


def test_cli_rejects_multiple_inputs_without_concat_dim(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """CLI rejects multi-path loader use when no concat dimension is defined."""
    loader_file = tmp_path / "loader_without_concat.py"
    loader_file.write_text("", encoding="utf-8")

    monkeypatch.setattr(xr, "open_dataset", lambda *args, **kwargs: _forecast_grid_ds())

    code = cli.main(
        [
            "a.nc",
            "b.nc",
            "--loader",
            str(loader_file),
            "--space",
            "grid",
            "--time",
            "forecast",
        ]
    )

    assert code is None
