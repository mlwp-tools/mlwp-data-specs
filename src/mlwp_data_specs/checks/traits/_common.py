"""Common helpers for structural trait checks."""

from __future__ import annotations

from typing import Literal

import xarray as xr

from mlwp_data_specs.specs.reporting import ValidationReport, log_function_call

AxisName = Literal["space", "time", "uncertainty"]

SECTION_MAP: dict[AxisName, str] = {
    "space": "Spatial Coordinate",
    "time": "Time Coordinate",
    "uncertainty": "Uncertainty",
}


@log_function_call
def check_dim_variants(
    ds: xr.Dataset,
    *,
    axis: AxisName,
    variants: list[set[str]],
) -> ValidationReport:
    """Validate that dataset dimensions match one allowed variant.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    axis : AxisName
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
def check_for_forbidden_dims(
    ds: xr.Dataset,
    *,
    axis: AxisName,
    forbidden_dims: set[str],
) -> ValidationReport:
    """Validate that the dataset has none of the given dimensions.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    axis : AxisName
        Trait axis key.
    forbidden_dims : set[str]
        Dimension names that the trait profile does not allow.

    Returns
    -------
    ValidationReport
        Report containing one PASS or FAIL result.
    """
    report = ValidationReport()
    requirement = "Forbidden dimensions are absent"

    present = forbidden_dims & set(ds.dims)
    if present:
        report.add(
            SECTION_MAP[axis],
            requirement,
            "FAIL",
            f"Dataset has dimensions not allowed for this profile: {sorted(present)}",
        )
    else:
        report.add(
            SECTION_MAP[axis],
            requirement,
            "PASS",
            f"None of {sorted(forbidden_dims)} is a dimension",
        )
    return report


@log_function_call
def check_leading_dim(
    ds: xr.Dataset,
    *,
    axis: AxisName,
    dim: str,
) -> ValidationReport:
    """Validate that ``dim`` is the first dimension of every data variable using it.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    axis : AxisName
        Trait axis key.
    dim : str
        Dimension that must be leftmost wherever it appears.

    Returns
    -------
    ValidationReport
        Report containing one PASS or FAIL result.
    """
    report = ValidationReport()
    requirement = f"'{dim}' is the leading dimension"

    misplaced = [
        f"{name} {var.dims}"
        for name, var in ds.data_vars.items()
        if dim in var.dims and var.dims[0] != dim
    ]
    if misplaced:
        report.add(
            SECTION_MAP[axis],
            requirement,
            "FAIL",
            f"'{dim}' must be the first dimension of: {'; '.join(misplaced)}",
        )
    else:
        report.add(
            SECTION_MAP[axis],
            requirement,
            "PASS",
            f"'{dim}' leads every data variable that has it",
        )
    return report


@log_function_call
def check_required_coords(
    ds: xr.Dataset,
    *,
    axis: AxisName,
    required_coords: set[str],
) -> ValidationReport:
    """Validate that required coordinates exist in the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    axis : AxisName
        Trait axis key.
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
