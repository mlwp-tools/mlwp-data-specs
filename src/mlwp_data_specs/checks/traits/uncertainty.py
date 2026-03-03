"""Structural checks for the uncertainty trait axis."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.checks.traits._common import (
    check_dim_variants,
    check_required_coords,
)
from mlwp_data_specs.traits.properties import Uncertainty
from mlwp_data_specs.traits.reporting import ValidationReport, log_function_call
from mlwp_data_specs.traits.specs import UNCERTAINTY_SPECS


@log_function_call
def check_uncertainty_trait_structure(
    ds: xr.Dataset,
    *,
    trait: Uncertainty,
) -> ValidationReport:
    """Run structural checks for the selected uncertainty trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : Uncertainty
        Selected uncertainty profile.

    Returns
    -------
    ValidationReport
        Combined report for uncertainty dimension and coordinate checks.
    """
    spec = UNCERTAINTY_SPECS[trait]
    report = ValidationReport()
    report += check_dim_variants(ds, axis="uncertainty", variants=spec.dim_variants)
    report += check_required_coords(
        ds,
        axis="uncertainty",
        required_coords=spec.required_coords,
    )
    return report
