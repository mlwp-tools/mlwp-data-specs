"""Structural checks for the space trait axis."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.checks.traits._common import (
    check_dim_variants,
    check_required_coords,
)
from mlwp_data_specs.traits.properties import Space
from mlwp_data_specs.traits.reporting import ValidationReport, log_function_call
from mlwp_data_specs.traits.specs import SPACE_SPECS


@log_function_call
def check_space_trait_structure(ds: xr.Dataset, *, trait: Space) -> ValidationReport:
    """Run structural checks for the selected space trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : Space
        Selected space profile.

    Returns
    -------
    ValidationReport
        Combined report for space dimension and coordinate checks.
    """
    spec = SPACE_SPECS[trait]
    report = ValidationReport()
    report += check_dim_variants(ds, axis="space", variants=spec.dim_variants)
    report += check_required_coords(
        ds, axis="space", required_coords=spec.required_coords
    )
    return report
