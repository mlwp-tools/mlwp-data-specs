import numpy as np
import xarray as xr

from mlwp_data_specs.traits.properties import Time
from mlwp_data_specs.traits.time_coordinate import validate_dataset


def _observation_ds(valid=True):
    ds = xr.Dataset(coords={"valid_time": ("valid_time", np.array(["2026-01-01T00:00:00"], dtype="datetime64[ns]"))})
    if valid:
        ds.coords["valid_time"].attrs["standard_name"] = "time"
    return ds


def test_time_observation_passes():
    report, _ = validate_dataset(_observation_ds(valid=True), trait=Time.OBSERVATION)
    assert not report.has_fails()


def test_time_observation_fails_without_standard_name():
    report, _ = validate_dataset(_observation_ds(valid=False), trait=Time.OBSERVATION)
    assert report.has_fails()
