"""Structural checks for the time trait axis."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.checks.traits._common import (
    check_dim_variants,
    check_required_coords,
)
from mlwp_data_specs.traits.properties import Time
from mlwp_data_specs.traits.reporting import ValidationReport, log_function_call
from mlwp_data_specs.traits.specs import TIME_SPECS


@log_function_call
def check_time_trait_structure(ds: xr.Dataset, *, trait: Time) -> ValidationReport:
    """Run structural checks for the selected time trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : Time
        Selected time profile.

    Returns
    -------
    ValidationReport
        Combined report for time dimension and coordinate checks.
    """
    spec = TIME_SPECS[trait]
    report = ValidationReport()
    report += check_dim_variants(ds, axis="time", variants=spec.dim_variants)
    report += check_required_coords(
        ds, axis="time", required_coords=spec.required_coords
    )
    return report
