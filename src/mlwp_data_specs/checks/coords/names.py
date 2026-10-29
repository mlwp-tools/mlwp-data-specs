"""Coordinate presence and attribute checks."""

from __future__ import annotations

from collections.abc import Iterable

import xarray as xr

from mlwp_data_specs.checks import SECTION_MAP, TraitAxis
from mlwp_data_specs.specs.reporting import ValidationReport, log_function_call


def _fmt_required(expected: Iterable[str]) -> str:
    """Format expected attribute values for report messages.

    Parameters
    ----------
    expected : Iterable[str]
        Expected values.

    Returns
    -------
    str
        Comma-separated value list.
    """
    return ", ".join(sorted(expected))


@log_function_call
def check_required_coords(
    ds: xr.Dataset,
    *,
    trait_axis: TraitAxis,
    required_coords: set[str],
) -> ValidationReport:
    """Validate that required coordinates exist in the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait_axis : TraitAxis
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
    section = SECTION_MAP[trait_axis]

    if not required_coords:
        report.add(section, requirement, "PASS", "No required coordinates")
        return report

    missing = required_coords - set(ds.coords)
    if missing:
        report.add(
            section,
            requirement,
            "FAIL",
            f"Missing required coordinates: {sorted(missing)}",
        )
    else:
        report.add(
            section,
            requirement,
            "PASS",
            f"All required coordinates present: {sorted(required_coords)}",
        )
    return report


@log_function_call
def check_coordinate_attrs(
    ds: xr.Dataset,
    *,
    section: str,
    requirement: str,
    coord: str,
    required_attrs: dict[str, set[str]],
) -> ValidationReport:
    """Validate required attributes for one coordinate.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    section : str
        Report section label.
    requirement : str
        Requirement text associated with this check.
    coord : str
        Coordinate name to validate.
    required_attrs : dict[str, set[str]]
        Mapping of attribute names to allowed values.

    Returns
    -------
    ValidationReport
        Report with a PASS/FAIL result for the coordinate.
    """
    report = ValidationReport()

    if coord not in ds.coords:
        report.add(section, requirement, "FAIL", f"Coordinate '{coord}' is missing")
        return report

    coord_attrs = ds.coords[coord].attrs
    failures: list[str] = []
    for attr_name, expected_values in required_attrs.items():
        value = coord_attrs.get(attr_name)
        if value is None:
            failures.append(f"missing attr '{attr_name}'")
            continue
        if str(value) not in expected_values:
            failures.append(
                f"attr '{attr_name}' is '{value}', expected one of [{_fmt_required(expected_values)}]"
            )

    if failures:
        report.add(section, requirement, "FAIL", f"{coord}: " + "; ".join(failures))
    else:
        report.add(section, requirement, "PASS", f"{coord}: metadata is compliant")
    return report
