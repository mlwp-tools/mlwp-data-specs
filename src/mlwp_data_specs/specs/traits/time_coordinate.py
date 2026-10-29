"""Executable specification for time-coordinate traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.coords.dimensions import check_dim_variants
from mlwp_data_specs.checks.coords.names import check_required_coords
from mlwp_data_specs.checks.coords.temporal import check_time_coordinate_metadata
from mlwp_data_specs.checks.global_attributes.traits import (
    TRAIT_ATTR_FORMAT,
    check_trait_attribute,
)
from mlwp_data_specs.specs.reporting import ValidationReport
from mlwp_data_specs.trait_profiles import Time

__all__ = ["IDENTIFIER", "TIME_TRAIT_ATTR", "VERSION", "Time", "validate_dataset"]

VERSION = "0.1.1-draft"
IDENTIFIER = "time_coordinate"
TIME_TRAIT_ATTR = TRAIT_ATTR_FORMAT.format("time")


def validate_dataset(
    ds: xr.Dataset | None, *, trait: str
) -> tuple[ValidationReport, str]:
    """Validate a dataset against the selected time trait specification.

    Parameters
    ----------
    ds : xr.Dataset | None
        Dataset to validate. ``None`` is only supported when checks are disabled
        (e.g. docs rendering mode via ``skip_all_checks``).
    trait : str
        Selected time trait profile, one of the `Time` members.

    Returns
    -------
    tuple[ValidationReport, str]
        Validation report and inline markdown specification text.
    """
    report = ValidationReport()

    spec_text = f"""
    ---
    version: {VERSION}
    trait: {IDENTIFIER}
    profile: {trait}
    ---

    ## 1. Introduction

    This document defines trait-level requirements for time coordinates in MLWP datasets.
    The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
    "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
    interpreted as described in RFC 2119.

    ## 2. Scope

    This specification applies to datasets validated with the `time={trait}`
    profile.

    ## 3. Structural Requirements

    ### 3.1 Accepted Dimension Variants
    """
    if trait == Time.FORECAST:
        spec_text += """
    - The dataset MUST include both `reference_time` and `lead_time` dimensions.
    """
        report += check_dim_variants(
            ds, trait_axis="time", variants=[{"reference_time", "lead_time"}]
        )
    elif trait == Time.OBSERVATION:
        spec_text += """
    - The dataset MUST include the `valid_time` dimension.
    """
        report += check_dim_variants(ds, trait_axis="time", variants=[{"valid_time"}])
    else:
        raise NotImplementedError(f"Unsupported time trait: {trait!r}")

    spec_text += """
    ### 3.2 Required Coordinates
    """
    if trait == Time.FORECAST:
        spec_text += """
    - The dataset MUST include the `lead_time` and `reference_time` coordinates.
    """
        report += check_required_coords(
            ds, trait_axis="time", required_coords={"reference_time", "lead_time"}
        )
    elif trait == Time.OBSERVATION:
        spec_text += """
    - The dataset MUST include the `valid_time` coordinate.
    """
        report += check_required_coords(
            ds, trait_axis="time", required_coords={"valid_time"}
        )
    else:
        raise NotImplementedError(f"Unsupported time trait: {trait!r}")

    spec_text += """
    ### 3.3 Optional Coordinates
    """
    if trait == Time.FORECAST:
        spec_text += """
    - The dataset MAY include optional coordinates for this profile:
      `['valid_time']`.
    """
    elif trait == Time.OBSERVATION:
        spec_text += """
    - The dataset MAY include optional coordinates for this profile:
      `[]`.
    """
    else:
        raise NotImplementedError(f"Unsupported time trait: {trait!r}")

    spec_text += """
    ## 4. Coordinate Metadata Requirements
    """
    if trait == Time.FORECAST:
        spec_text += """
    - `reference_time` MUST have `standard_name` equal to `forecast_reference_time` or `time`.
    - `lead_time` MUST have `standard_name` equal to `forecast_period`.
    - `lead_time` MUST have `units` in one of: `s`, `seconds`, `h`, `hours`.
    - If `valid_time` is present, it MUST have `standard_name` equal to `time`.
    """
    elif trait == Time.OBSERVATION:
        spec_text += """
    - `valid_time` MUST have `standard_name` equal to `time`.
    """
    else:
        raise NotImplementedError(f"Unsupported time trait: {trait!r}")

    report += check_time_coordinate_metadata(ds, trait=trait)

    allowed = ", ".join(f"`{profile}`" for profile in Time)
    spec_text += f"""
    ## 5. Global Attributes

    - The dataset MAY include the global attribute `{TIME_TRAIT_ATTR}` to declare its
      time trait profile.
    - If present, `{TIME_TRAIT_ATTR}` MUST be one of: {allowed}.
    - If present, `{TIME_TRAIT_ATTR}` SHOULD equal `{trait}`, the profile being
      validated.
    - The requirement on the value of `{TIME_TRAIT_ATTR}` applies to any dataset
      that carries the attribute, including datasets validated only against other
      traits.
    """
    report += check_trait_attribute(ds, trait_axis="time", trait_cls=Time, trait=trait)

    return report, textwrap.dedent(spec_text)
