"""Coordinate metadata checks across trait axes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import xarray as xr

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
def check_coordinate_attrs(
    ds: xr.Dataset,
    *,
    section: str,
    requirement: str,
    coord: str,
    required_attrs: dict[str, set[str]],
    failure_status: Literal["FAIL", "WARNING"] = "FAIL",
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
    failure_status : {"FAIL", "WARNING"}, optional
        Status reported when the coordinate or an attribute does not comply.
        Use ``"WARNING"`` for recommended (SHOULD) attributes.

    Returns
    -------
    ValidationReport
        Report with a PASS or ``failure_status`` result for the coordinate.
    """
    report = ValidationReport()

    if coord not in ds.coords:
        report.add(
            section, requirement, failure_status, f"Coordinate '{coord}' is missing"
        )
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
        report.add(
            section, requirement, failure_status, f"{coord}: " + "; ".join(failures)
        )
    else:
        report.add(section, requirement, "PASS", f"{coord}: metadata is compliant")
    return report


@log_function_call
def check_space_coordinate_metadata(
    ds: xr.Dataset, *, trait: object
) -> ValidationReport:
    """Validate coordinate metadata for the selected space trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : object
        Selected space profile enum instance (or enum-like object with a
        ``value`` attribute).

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
    trait_value = str(getattr(trait, "value", trait))
    if trait_value == "grid":
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
def check_time_coordinate_metadata(
    ds: xr.Dataset, *, trait: object
) -> ValidationReport:
    """Validate coordinate metadata for the selected time trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : object
        Selected time profile enum instance (or enum-like object with a
        ``value`` attribute).

    Returns
    -------
    ValidationReport
        Combined report for all required time coordinates.
    """
    report = ValidationReport()
    section = "Time Coordinate"

    expectations: dict[str, dict[str, set[str]]] = {}
    trait_value = str(getattr(trait, "value", trait))
    if trait_value == "observation":
        expectations["valid_time"] = {
            "standard_name": {"time"},
        }
    elif trait_value == "forecast":
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

    if "valid_time" in ds.coords and trait_value == "forecast":
        report += check_coordinate_attrs(
            ds,
            section=section,
            requirement="Metadata for coordinate 'valid_time'",
            coord="valid_time",
            required_attrs={"standard_name": {"time"}},
        )

    return report


@log_function_call
def check_member_coordinate_values(ds: xr.Dataset) -> ValidationReport:
    """Validate the structure and values of the ensemble ``member`` coordinate.

    ``member`` must be one-dimensional on the ``member`` dimension, with unique
    integer values. String labels (as earthkit-data emits by default) fail.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.

    Returns
    -------
    ValidationReport
        Report for the coordinate's shape, uniqueness and dtype. Empty when the
        coordinate is missing, which ``check_required_coords`` reports.
    """
    report = ValidationReport()
    section = "Uncertainty"

    if "member" not in ds.coords:
        return report

    member = ds.coords["member"]
    if member.dims != ("member",):
        report.add(
            section,
            "Member coordinate is 1-D on 'member'",
            "FAIL",
            f"member has dims {member.dims}, expected ('member',)",
        )
        return report

    index = member.to_index()
    if index.is_unique:
        report.add(
            section,
            "Member values are unique",
            "PASS",
            f"{index.size} unique member values",
        )
    else:
        duplicates = sorted(set(index[index.duplicated()].tolist()))
        report.add(
            section,
            "Member values are unique",
            "FAIL",
            f"Duplicate member values: {duplicates}",
        )

    if member.dtype.kind in "iu":
        report.add(
            section,
            "Member values are integers",
            "PASS",
            f"member has integer dtype {member.dtype}",
        )
    else:
        report.add(
            section,
            "Member values are integers",
            "FAIL",
            f"member has dtype {member.dtype}; expected an integer dtype",
        )

    return report


@log_function_call
def check_uncertainty_coordinate_metadata(
    ds: xr.Dataset,
    *,
    trait: object,
) -> ValidationReport:
    """Validate coordinate metadata for the selected uncertainty trait.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait : object
        Selected uncertainty profile enum instance (or enum-like object with a
        ``value`` attribute).

    Returns
    -------
    ValidationReport
        Report for uncertainty coordinate metadata and bounds checks.
    """
    report = ValidationReport()
    section = "Uncertainty"

    trait_value = str(getattr(trait, "value", trait))
    if trait_value == "deterministic":
        report.add(
            section,
            "Deterministic mode metadata",
            "PASS",
            "No uncertainty coordinate required",
        )
        return report

    if trait_value == "ensemble":
        report += check_coordinate_attrs(
            ds,
            section=section,
            requirement="Metadata for coordinate 'member'",
            coord="member",
            required_attrs={"standard_name": {"realization"}},
        )
        if "member" in ds.coords:
            report += check_coordinate_attrs(
                ds,
                section=section,
                requirement="Recommended metadata for coordinate 'member'",
                coord="member",
                required_attrs={"units": {"1"}},
                failure_status="WARNING",
            )
        return report

    report += check_coordinate_attrs(
        ds,
        section=section,
        requirement="Metadata for coordinate 'quantile'",
        coord="quantile",
        required_attrs={"units": {"1"}},
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
