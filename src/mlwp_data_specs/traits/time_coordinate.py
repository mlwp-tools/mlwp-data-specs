"""Executable specification for time-coordinate traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import check_time_coordinate_metadata
from mlwp_data_specs.checks.traits.structure import check_time_trait_structure
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
    spec_text = f"""
    ---
    trait: {IDENTIFIER}
    profile: {trait.value}
    version: {VERSION}
    ---

    ## 1. Scope

    This specification enforces time-coordinate trait conformance for machine-learning weather datasets.

    ## 2. Structural Requirements

    - The dataset MUST provide required time dimensions and coordinate names for the selected time trait profile.
    """

    report += check_time_trait_structure(ds, trait=trait)

    spec_text += """
    ## 3. Coordinate Metadata Requirements

    - Time coordinates MUST expose CF-compatible metadata.
    - `standard_name` MUST be set for required time coordinates.
    - For forecast lead times, units MUST indicate elapsed time.
    """

    report += check_time_coordinate_metadata(ds, trait=trait)

    return report, textwrap.dedent(spec_text)
