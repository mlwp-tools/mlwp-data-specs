"""Executable specification for time-coordinate traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import check_time_coordinate_metadata
from mlwp_data_specs.checks.traits.time import check_time_trait_structure
from mlwp_data_specs.traits.properties import Time
from mlwp_data_specs.traits.reporting import ValidationReport

VERSION = "0.1.0"
IDENTIFIER = "time_coordinate"


def validate_dataset(ds: xr.Dataset | None, *, trait: Time) -> tuple[ValidationReport, str]:
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
    if trait == Time.FORECAST:
        structural_requirements = """
    - Accepted dimension variant is: `{'reference_time', 'lead_time'}`.
    - Required coordinates are: `reference_time`, `lead_time`.
    - Optional coordinate is: `valid_time`.
    """
        metadata_requirements = """
    - `reference_time` MUST have `standard_name` equal to `forecast_reference_time` or `time`.
    - `lead_time` MUST have `standard_name` equal to `forecast_period`.
    - `lead_time` MUST have `units` in one of: `s`, `seconds`, `h`, `hours`.
    - If `valid_time` is present, it MUST have `standard_name` equal to `time`.
    """
    else:
        structural_requirements = """
    - Accepted dimension variant is: `{'valid_time'}`.
    - Required coordinate is: `valid_time`.
    """
        metadata_requirements = """
    - `valid_time` MUST have `standard_name` equal to `time`.
    """

    spec_text = f"""
    ---
    trait: {IDENTIFIER}
    profile: {trait.value}
    version: {VERSION}
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

    {structural_requirements}
    """

    report += check_time_trait_structure(ds, trait=trait)

    spec_text += f"""
    ## 4. Coordinate Metadata Requirements

    {metadata_requirements}
    """

    report += check_time_coordinate_metadata(ds, trait=trait)

    return report, textwrap.dedent(spec_text)
