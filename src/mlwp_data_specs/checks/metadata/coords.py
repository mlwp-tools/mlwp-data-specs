"""Coordinate metadata checks across trait axes."""

from __future__ import annotations

from collections.abc import Iterable

import xarray as xr

from mlwp_data_specs.traits.properties import Space, Time, Uncertainty
from mlwp_data_specs.traits.reporting import ValidationReport, log_function_call


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


@log_function_call
def check_space_coordinate_metadata(
    ds: xr.Dataset, *, trait: Space
) -> ValidationReport:
    """Validate coordinate metadata for the selected space trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : Space
        Selected space profile.

    Returns
    -------
    ValidationReport
        Combined report for all relevant spatial coordinates.
    """
    report = ValidationReport()
    section = "Spatial Coordinate"

    expectations = {
        "longitude": {
            "standard_name": {"longitude"},
            "units": {"degrees_east"},
        },
        "latitude": {
            "standard_name": {"latitude"},
            "units": {"degrees_north"},
        },
    }
    if trait == Space.GRID:
        expectations.update(
            {
                "xc": {
                    "standard_name": {"projection_x_coordinate"},
                    "units": {"m", "meter", "metre"},
                },
                "yc": {
                    "standard_name": {"projection_y_coordinate"},
                    "units": {"m", "meter", "metre"},
                },
            }
        )

    for coord, required_attrs in expectations.items():
        if coord not in ds.coords and coord in {"xc", "yc"}:
            continue
        report += check_coordinate_attrs(
            ds,
            section=section,
            requirement=f"Metadata for coordinate '{coord}'",
            coord=coord,
            required_attrs=required_attrs,
        )

    return report


@log_function_call
def check_time_coordinate_metadata(ds: xr.Dataset, *, trait: Time) -> ValidationReport:
    """Validate coordinate metadata for the selected time trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : Time
        Selected time profile.

    Returns
    -------
    ValidationReport
        Combined report for all required time coordinates.
    """
    report = ValidationReport()
    section = "Time Coordinate"

    expectations: dict[str, dict[str, set[str]]] = {}
    if trait == Time.OBSERVATION:
        expectations["valid_time"] = {
            "standard_name": {"time"},
        }
    elif trait == Time.FORECAST:
        expectations.update(
            {
                "reference_time": {
                    "standard_name": {"forecast_reference_time", "time"},
                },
                "lead_time": {
                    "standard_name": {"forecast_period"},
                    "units": {"s", "seconds", "h", "hours"},
                },
            }
        )

    for coord, required_attrs in expectations.items():
        report += check_coordinate_attrs(
            ds,
            section=section,
            requirement=f"Metadata for coordinate '{coord}'",
            coord=coord,
            required_attrs=required_attrs,
        )

    if "valid_time" in ds.coords and trait == Time.FORECAST:
        report += check_coordinate_attrs(
            ds,
            section=section,
            requirement="Metadata for coordinate 'valid_time'",
            coord="valid_time",
            required_attrs={"standard_name": {"time"}},
        )

    return report


@log_function_call
def check_uncertainty_coordinate_metadata(
    ds: xr.Dataset,
    *,
    trait: Uncertainty,
) -> ValidationReport:
    """Validate coordinate metadata for the selected uncertainty trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : Uncertainty
        Selected uncertainty profile.

    Returns
    -------
    ValidationReport
        Report for uncertainty coordinate metadata and bounds checks.
    """
    report = ValidationReport()
    section = "Uncertainty"

    if trait == Uncertainty.DETERMINISTIC:
        report.add(
            section,
            "Deterministic mode metadata",
            "PASS",
            "No uncertainty coordinate required",
        )
        return report

    if trait == Uncertainty.ENSEMBLE:
        report += check_coordinate_attrs(
            ds,
            section=section,
            requirement="Metadata for coordinate 'member'",
            coord="member",
            required_attrs={"standard_name": {"realization"}},
        )
        return report

    report += check_coordinate_attrs(
        ds,
        section=section,
        requirement="Metadata for coordinate 'quantile'",
        coord="quantile",
        required_attrs={"standard_name": {"quantile"}, "units": {"1"}},
    )

    if "quantile" not in ds.coords:
        return report

    quantile_values = ds.coords["quantile"].values
    invalid = [float(v) for v in quantile_values if float(v) < 0.0 or float(v) > 1.0]
    if invalid:
        report.add(
            section,
            "Quantile bounds",
            "FAIL",
            f"Quantile values must be in [0, 1], found {invalid}",
        )
    else:
        report.add(section, "Quantile bounds", "PASS", "All quantiles are in [0, 1]")

    return report
