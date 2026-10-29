"""Executable specification for uncertainty traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.coords.dimensions import check_dim_variants
from mlwp_data_specs.checks.coords.names import check_required_coords
from mlwp_data_specs.checks.coords.uncertainty import (
    check_uncertainty_coordinate_metadata,
)
from mlwp_data_specs.checks.global_attributes.traits import (
    TRAIT_ATTR_FORMAT,
    check_trait_attribute,
)
from mlwp_data_specs.specs.reporting import ValidationReport
from mlwp_data_specs.trait_profiles import Uncertainty

__all__ = [
    "IDENTIFIER",
    "UNCERTAINTY_TRAIT_ATTR",
    "VERSION",
    "Uncertainty",
    "validate_dataset",
]

VERSION = "0.1.1-draft"
IDENTIFIER = "uncertainty"
UNCERTAINTY_TRAIT_ATTR = TRAIT_ATTR_FORMAT.format("uncertainty")


def validate_dataset(
    ds: xr.Dataset | None, *, trait: str
) -> tuple[ValidationReport, str]:
    """Validate a dataset against the selected uncertainty trait specification.

    Parameters
    ----------
    ds : xr.Dataset | None
        Dataset to validate. ``None`` is only supported when checks are disabled
        (e.g. docs rendering mode via ``skip_all_checks``).
    trait : str
        Selected uncertainty trait profile, one of the `Uncertainty` members.

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

    This document defines trait-level requirements for uncertainty representation in
    MLWP datasets. The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
    "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are
    to be interpreted as described in RFC 2119.

    ## 2. Scope

    This specification applies to datasets validated with the
    `uncertainty={trait}` profile.

    ## 3. Structural Requirements

    ### 3.1 Accepted Dimension Variants
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - No uncertainty-specific dimensions are required for this profile.
    """
        report += check_dim_variants(ds, trait_axis="uncertainty", variants=[])
    elif trait == Uncertainty.ENSEMBLE:
        spec_text += """
    - The dataset MUST include the `member` dimension for uncertainty realizations.
    """
        report += check_dim_variants(
            ds, trait_axis="uncertainty", variants=[{"member"}]
        )
    elif trait == Uncertainty.QUANTILE:
        spec_text += """
    - The dataset MUST include the `quantile` dimension for uncertainty representation.
    """
        report += check_dim_variants(
            ds, trait_axis="uncertainty", variants=[{"quantile"}]
        )
    else:
        raise NotImplementedError(f"Unsupported uncertainty trait: {trait!r}")

    spec_text += """
    ### 3.2 Required Coordinates
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - This profile defines no required uncertainty coordinates.
    """
        report += check_required_coords(
            ds, trait_axis="uncertainty", required_coords=set()
        )
    elif trait == Uncertainty.ENSEMBLE:
        spec_text += """
    - The dataset MUST include the `member` coordinate.
    """
        report += check_required_coords(
            ds, trait_axis="uncertainty", required_coords={"member"}
        )
    elif trait == Uncertainty.QUANTILE:
        spec_text += """
    - The dataset MUST include the `quantile` coordinate.
    """
        report += check_required_coords(
            ds, trait_axis="uncertainty", required_coords={"quantile"}
        )
    else:
        raise NotImplementedError(f"Unsupported uncertainty trait: {trait!r}")

    spec_text += """
    ### 3.3 Optional Coordinates

    - The dataset MAY include optional coordinates for this profile: `[]`.

    ### 3.4 Optional Dimensions

    - The dataset MAY include optional dimensions for this profile: `[]`.

    ## 4. Coordinate Metadata Requirements
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - No uncertainty coordinate metadata is required.
    """
    elif trait == Uncertainty.ENSEMBLE:
        spec_text += """
    - `member` MUST have `standard_name` equal to `realization`.
    """
    elif trait == Uncertainty.QUANTILE:
        spec_text += """
    - `quantile` MUST have `standard_name` equal to `quantile`.
    - `quantile` MUST have `units` equal to `1`.
    - All `quantile` coordinate values MUST be within `[0, 1]`.
    """
    else:
        raise NotImplementedError(f"Unsupported uncertainty trait: {trait!r}")

    report += check_uncertainty_coordinate_metadata(ds, trait=trait)

    allowed = ", ".join(f"`{profile}`" for profile in Uncertainty)
    spec_text += f"""
    ## 5. Global Attributes

    - The dataset MAY include the global attribute `{UNCERTAINTY_TRAIT_ATTR}` to
      declare its uncertainty trait profile.
    - If present, `{UNCERTAINTY_TRAIT_ATTR}` MUST be one of: {allowed}.
    - If present, `{UNCERTAINTY_TRAIT_ATTR}` SHOULD equal `{trait}`, the
      profile being validated.
    - The requirement on the value of `{UNCERTAINTY_TRAIT_ATTR}` applies to any
      dataset that carries the attribute, including datasets validated only
      against other traits.
    """
    report += check_trait_attribute(
        ds, trait_axis="uncertainty", trait_cls=Uncertainty, trait=trait
    )

    return report, textwrap.dedent(spec_text)
