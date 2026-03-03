"""Structural trait checks based on allowed dims and required coordinates."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.traits.properties import Space, Time, Uncertainty
from mlwp_data_specs.traits.reporting import ValidationReport, log_function_call
from mlwp_data_specs.traits.specs import SPACE_SPECS, TIME_SPECS, UNCERTAINTY_SPECS


SECTION_MAP = {
    "space": "Spatial Coordinate",
    "time": "Time Coordinate",
    "uncertainty": "Uncertainty",
}


@log_function_call
def check_dim_variants(
    ds: xr.Dataset,
    *,
    axis: str,
    variants: list[set[str]],
) -> ValidationReport:
    """Validate that dataset dimensions match one allowed variant.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    axis : str
        Trait axis key (``space``, ``time``, ``uncertainty``).
    variants : list[set[str]]
        Allowed dimension sets for the selected trait profile.

    Returns
    -------
    ValidationReport
        Report containing one PASS or FAIL result.
    """
    report = ValidationReport()
    requirement = "Allowed dimension variants"

    if not variants:
        report.add(SECTION_MAP[axis], requirement, "PASS", "No dimension restrictions")
        return report

    ds_dims = set(ds.dims)
    for variant in variants:
        if variant.issubset(ds_dims):
            report.add(
                SECTION_MAP[axis],
                requirement,
                "PASS",
                f"Dataset dims satisfy variant {sorted(variant)}",
            )
            return report

    report.add(
        SECTION_MAP[axis],
        requirement,
        "FAIL",
        f"Dataset dims {sorted(ds_dims)} do not match any allowed variants",
    )
    return report


@log_function_call
def check_required_coords(
    ds: xr.Dataset,
    *,
    axis: str,
    required_coords: set[str],
) -> ValidationReport:
    """Validate that required coordinates exist in the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    axis : str
        Trait axis key (``space``, ``time``, ``uncertainty``).
    required_coords : set[str]
        Required coordinate names for the trait profile.

    Returns
    -------
    ValidationReport
        Report containing one PASS or FAIL result.
    """
    report = ValidationReport()
    requirement = "Required coordinates are present"

    if not required_coords:
        report.add(SECTION_MAP[axis], requirement, "PASS", "No required coordinates")
        return report

    missing = required_coords - set(ds.coords)
    if missing:
        report.add(
            SECTION_MAP[axis],
            requirement,
            "FAIL",
            f"Missing required coordinates: {sorted(missing)}",
        )
    else:
        report.add(
            SECTION_MAP[axis],
            requirement,
            "PASS",
            f"All required coordinates present: {sorted(required_coords)}",
        )
    return report


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
    report += check_required_coords(ds, axis="space", required_coords=spec.required_coords)
    return report


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
    report += check_required_coords(ds, axis="time", required_coords=spec.required_coords)
    return report


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
