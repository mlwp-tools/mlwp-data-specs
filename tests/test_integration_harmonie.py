from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
import xarray as xr

from mlwp_data_specs.traits.properties import Space, Time
from mlwp_data_specs.traits.spatial_coordinate import validate_dataset as validate_space
from mlwp_data_specs.traits.time_coordinate import validate_dataset as validate_time


def _latest_analysis_time(now_utc: datetime) -> datetime:
    candidate = now_utc - timedelta(hours=6)
    rounded_hour = (candidate.hour // 3) * 3
    return candidate.replace(hour=rounded_hour, minute=0, second=0, microsecond=0)


def _dataset_url(now_utc: datetime) -> str:
    analysis_time = _latest_analysis_time(now_utc)
    ts = analysis_time.strftime("%Y-%m-%dT%H0000Z")
    return f"https://harmonie-zarr.s3.amazonaws.com/dini/control/{ts}/single_levels.zarr"


@pytest.mark.integration
def test_harmonie_forecast_grid_dataset_integration():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run remote integration tests")

    now_utc = datetime.now(timezone.utc)
    url = _dataset_url(now_utc)

    ds = xr.open_zarr(url)

    time_report, _ = validate_time(ds, trait=Time.FORECAST)
    space_report, _ = validate_space(ds, trait=Space.GRID)

    combined = time_report + space_report
    assert not combined.has_fails(), f"Validation failed for URL: {url}"
