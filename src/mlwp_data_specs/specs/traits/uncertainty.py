"""Executable specification for uncertainty traits."""

from __future__ import annotations

import textwrap
from enum import Enum

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import (
    check_member_coordinate_values,
    check_uncertainty_coordinate_metadata,
)
from mlwp_data_specs.checks.traits._common import (
    check_dim_variants,
    check_forbidden_dims,
    check_required_coords,
)
from mlwp_data_specs.specs.reporting import ValidationReport

VERSION = "0.2.0"
IDENTIFIER = "uncertainty"


class Uncertainty(str, Enum):
    """Supported uncertainty trait profiles."""

    DETERMINISTIC = "deterministic"
    ENSEMBLE = "ensemble"
    QUANTILE = "quantile"


def validate_dataset(
    ds: xr.Dataset | None, *, trait: Uncertainty
) -> tuple[ValidationReport, str]:
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

    spec_text = f"""
    ---
    version: {VERSION}
    trait: {IDENTIFIER}
    profile: {trait.value}
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

    ### 3.1 Accepted Dimension Variants
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - No uncertainty-specific dimensions are required for this profile.
    - The dataset MUST NOT have a `member` or `quantile` dimension.
    """
        report += check_dim_variants(ds, axis="uncertainty", variants=[])
        report += check_forbidden_dims(
            ds, axis="uncertainty", forbidden_dims={"member", "quantile"}
        )
    elif trait == Uncertainty.ENSEMBLE:
        spec_text += """
    - The dataset MUST include the `member` dimension for uncertainty realizations.
    """
        report += check_dim_variants(ds, axis="uncertainty", variants=[{"member"}])
    elif trait == Uncertainty.QUANTILE:
        spec_text += """
    - The dataset MUST include the `quantile` dimension for uncertainty representation.
    """
        report += check_dim_variants(ds, axis="uncertainty", variants=[{"quantile"}])
    else:
        raise NotImplementedError(f"Unsupported uncertainty trait: {trait!r}")

    spec_text += """
    ### 3.2 Required Coordinates
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - This profile defines no required uncertainty coordinates.
    """
        report += check_required_coords(ds, axis="uncertainty", required_coords=set())
    elif trait == Uncertainty.ENSEMBLE:
        spec_text += """
    - The dataset MUST include the `member` coordinate.
    - `member` MUST be a one-dimensional coordinate variable on the `member`
      dimension, and its values MUST be unique.
    - `member` SHOULD have an integer dtype. Its values SHOULD be the producer's
      member identifiers (e.g. GRIB `perturbationNumber`, where 0 is the control
      member) rather than positional indices; they need not start at 0 or be
      contiguous.
    """
        report += check_required_coords(
            ds, axis="uncertainty", required_coords={"member"}
        )
        report += check_member_coordinate_values(ds)
    elif trait == Uncertainty.QUANTILE:
        spec_text += """
    - The dataset MUST include the `quantile` coordinate.
    """
        report += check_required_coords(
            ds, axis="uncertainty", required_coords={"quantile"}
        )
    else:
        raise NotImplementedError(f"Unsupported uncertainty trait: {trait!r}")

    spec_text += """
    ### 3.3 Optional Coordinates
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - The dataset MAY include a scalar `member` coordinate identifying a single
      member selected from an ensemble (CF §5.7).
    """
    else:
        spec_text += """
    - The dataset MAY include optional coordinates for this profile: `[]`.
    """

    spec_text += """
    ### 3.4 Optional Dimensions

    - The dataset MAY include optional dimensions for this profile: `[]`.
    """

    if trait in (Uncertainty.ENSEMBLE, Uncertainty.QUANTILE):
        dim = "member" if trait == Uncertainty.ENSEMBLE else "quantile"
        spec_text += f"""
    ### 3.5 Dimension Order

    - The `{dim}` dimension SHOULD be placed to the left of the time and spatial
      dimensions, e.g. `({dim}, reference_time, lead_time, grid_index)`, following
      CF §2.4. This recommendation is not checked.
    """

    spec_text += """
    ## 4. Coordinate Metadata Requirements
    """
    if trait == Uncertainty.DETERMINISTIC:
        spec_text += """
    - No uncertainty coordinate metadata is required.
    - If the data were derived by reducing an ensemble over `member` (e.g. an
      ensemble mean or spread), the data variables SHOULD record this in
      `cell_methods`, e.g. `realization: mean` (CF §7.3.4). This recommendation
      is not checked.
    """
    elif trait == Uncertainty.ENSEMBLE:
        spec_text += """
    - `member` MUST have `standard_name` equal to `realization`.
    - `member` SHOULD have `units` equal to `1`, the canonical units of
      `realization`.
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

    return report, textwrap.dedent(spec_text)
