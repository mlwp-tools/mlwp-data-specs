"""Executable specification for time-coordinate traits."""

from __future__ import annotations

import textwrap
from enum import Enum

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import check_time_coordinate_metadata
from mlwp_data_specs.checks.traits._common import (
    check_dim_variants,
    check_required_coords,
)
from mlwp_data_specs.specs.reporting import ValidationReport

VERSION = "0.1.0"
IDENTIFIER = "time_coordinate"


class Time(str, Enum):
    """Supported temporal trait profiles."""

    FORECAST = "forecast"
    OBSERVATION = "observation"


def validate_dataset(
    ds: xr.Dataset | None, *, trait: Time
) -> tuple[ValidationReport, str]:
    """Validate a dataset against the selected time trait specification.

    Parameters
    ----------
    ds : xr.Dataset | None
        Dataset to validate. ``None`` is only supported when checks are disabled
        (e.g. docs rendering mode via ``skip_all_checks``).
    trait : Time
        Selected time trait profile.

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
    profile: {trait.value}
    ---

    ## 1. Introduction

    This document defines trait-level requirements for time coordinates in MLWP datasets.
    The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
    "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
    interpreted as described in RFC 2119.

    ## 2. Scope

    This specification applies to datasets validated with the `time={trait.value}`
    profile.

    ## 3. Structural Requirements

    ### 3.1 Accepted Dimension Variants
    """
    if trait == Time.FORECAST:
        spec_text += """
    - The dataset MUST match one accepted dimension variant for this profile:
      `[{'reference_time', 'lead_time'}]`.
    """
        report += check_dim_variants(
            ds, axis="time", variants=[{"reference_time", "lead_time"}]
        )
    elif trait == Time.OBSERVATION:
        spec_text += """
    - The dataset MUST match one accepted dimension variant for this profile:
      `[{'valid_time'}]`.
    """
        report += check_dim_variants(ds, axis="time", variants=[{"valid_time"}])
    else:
        raise NotImplementedError(f"Unsupported time trait: {trait!r}")

    spec_text += """
    ### 3.2 Required Coordinates
    """
    if trait == Time.FORECAST:
        spec_text += """
    - The dataset MUST include required coordinates for this profile:
      `['lead_time', 'reference_time']`.
    """
        report += check_required_coords(
            ds, axis="time", required_coords={"reference_time", "lead_time"}
        )
    elif trait == Time.OBSERVATION:
        spec_text += """
    - The dataset MUST include required coordinates for this profile:
      `['valid_time']`.
    """
        report += check_required_coords(ds, axis="time", required_coords={"valid_time"})
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

    return report, textwrap.dedent(spec_text)
