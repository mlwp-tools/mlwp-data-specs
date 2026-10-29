"""Dimension checks."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.checks import SECTION_MAP, TraitAxis
from mlwp_data_specs.specs.reporting import ValidationReport, log_function_call


@log_function_call
def check_dim_variants(
    ds: xr.Dataset,
    *,
    trait_axis: TraitAxis,
    variants: list[set[str]],
) -> ValidationReport:
    """Validate that dataset dimensions match one allowed variant.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait_axis : TraitAxis
        Trait axis key.
    variants : list[set[str]]
        Allowed dimension sets for the selected trait profile.

    Returns
    -------
    ValidationReport
        Report containing one PASS or FAIL result.
    """
    report = ValidationReport()
    requirement = "Allowed dimension variants"
    section = SECTION_MAP[trait_axis]

    if not variants:
        report.add(section, requirement, "PASS", "No dimension restrictions")
        return report

    ds_dims = set(ds.dims)
    for variant in variants:
        if variant.issubset(ds_dims):
            report.add(
                section,
                requirement,
                "PASS",
                f"Dataset dims satisfy variant {sorted(variant)}",
            )
            return report

    report.add(
        section,
        requirement,
        "FAIL",
        f"Dataset dims {sorted(ds_dims)} do not match any allowed variants",
    )
    return report
