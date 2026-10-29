"""Checks on global attributes declaring dataset trait profiles."""

from __future__ import annotations

import xarray as xr

from mlwp_data_specs.checks import SECTION_MAP, TraitAxis
from mlwp_data_specs.specs.reporting import ValidationReport, log_function_call
from mlwp_data_specs.trait_profiles import StrEnumLike

TRAIT_ATTR_FORMAT = "mlwp_{}_trait"


@log_function_call
def check_trait_attribute(
    ds: xr.Dataset,
    *,
    trait_axis: TraitAxis,
    trait_cls: type[StrEnumLike],
    trait: str | None = None,
) -> ValidationReport:
    """Validate the optional global attribute declaring a trait profile.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset being validated.
    trait_axis : TraitAxis
        Trait axis key, used to build the attribute name (e.g.
        ``mlwp_time_trait``).
    trait_cls : type[StrEnumLike]
        Class listing the valid profiles for this trait axis.
    trait : str | None, optional
        Trait profile the dataset is being validated against, one of the
        ``trait_cls`` members. If ``None``, only the validity of the attribute
        value is checked.

    Returns
    -------
    ValidationReport
        PASS if the attribute is absent, or valid and (when ``trait`` is given)
        matching ``trait``; FAIL if it is not a valid profile value; WARNING if
        it names a different valid profile than ``trait``.
    """
    report = ValidationReport()
    section = SECTION_MAP[trait_axis]
    attr_name = TRAIT_ATTR_FORMAT.format(trait_axis)
    requirement = f"Global attribute '{attr_name}'"

    value = ds.attrs.get(attr_name)
    if value is None:
        report.add(section, requirement, "PASS", "Optional attribute not set")
        return report

    if value not in trait_cls:
        report.add(
            section,
            requirement,
            "FAIL",
            f"Value '{value}' is not one of {list(trait_cls)}",
        )
        return report

    if trait is None:
        report.add(section, requirement, "PASS", f"Value '{value}' is valid")
    elif value != trait:
        report.add(
            section,
            requirement,
            "WARNING",
            f"Value '{value}' differs from validated profile '{trait}'",
        )
    else:
        report.add(section, requirement, "PASS", f"Value '{value}' matches profile")
    return report
