"""Executable specification for uncertainty traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import check_uncertainty_coordinate_metadata
from mlwp_data_specs.checks.traits.uncertainty import check_uncertainty_trait_structure
from mlwp_data_specs.traits.properties import Uncertainty
from mlwp_data_specs.traits.reporting import ValidationReport

VERSION = "0.1.0"
IDENTIFIER = "uncertainty"


def validate_dataset(ds: xr.Dataset | None, *, trait: Uncertainty) -> tuple[ValidationReport, str]:
    """Validate a dataset against the selected uncertainty trait specification.

    Parameters
    ----------
    ds : xr.Dataset | None
        Dataset to validate. ``None`` is only supported when checks are disabled
        (e.g. docs rendering mode via ``skip_all_checks``).
    trait : Uncertainty
        Selected uncertainty trait profile.

    Returns
    -------
    tuple[ValidationReport, str]
        Validation report and inline markdown specification text.
    """
    report = ValidationReport()
    if trait == Uncertainty.DETERMINISTIC:
        structural_requirements = """
    - No uncertainty-specific dimensions or coordinates are required.
    """
        metadata_requirements = """
    - No uncertainty coordinate metadata is required.
    """
    elif trait == Uncertainty.ENSEMBLE:
        structural_requirements = """
    - Accepted dimension variant is: `{'member'}`.
    - Required coordinate is: `member`.
    """
        metadata_requirements = """
    - `member` MUST have `standard_name` equal to `realization`.
    """
    else:
        structural_requirements = """
    - Accepted dimension variant is: `{'quantile'}`.
    - Required coordinate is: `quantile`.
    """
        metadata_requirements = """
    - `quantile` MUST have `standard_name` equal to `quantile`.
    - `quantile` MUST have `units` equal to `1`.
    - All `quantile` coordinate values MUST be within `[0, 1]`.
    """

    spec_text = f"""
    ---
    trait: {IDENTIFIER}
    profile: {trait.value}
    version: {VERSION}
    ---

    ## 1. Introduction

    This document defines trait-level requirements for uncertainty representation in
    MLWP datasets. The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
    "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are
    to be interpreted as described in RFC 2119.

    ## 2. Scope

    This specification applies to datasets validated with the
    `uncertainty={trait.value}` profile.

    ## 3. Structural Requirements

    {structural_requirements}
    """

    report += check_uncertainty_trait_structure(ds, trait=trait)

    spec_text += f"""
    ## 4. Coordinate Metadata Requirements

    {metadata_requirements}
    """

    report += check_uncertainty_coordinate_metadata(ds, trait=trait)

    return report, textwrap.dedent(spec_text)
