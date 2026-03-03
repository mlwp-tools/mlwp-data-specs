"""Executable specification for spatial-coordinate traits."""

from __future__ import annotations

import textwrap
from enum import Enum

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import check_space_coordinate_metadata
from mlwp_data_specs.checks.traits._common import (
    check_dim_variants,
    check_required_coords,
)
from mlwp_data_specs.specs.reporting import ValidationReport

VERSION = "0.1.0"
IDENTIFIER = "spatial_coordinate"


class Space(str, Enum):
    """Supported spatial trait profiles."""

    GRID = "grid"
    POINT = "point"


def validate_dataset(
    ds: xr.Dataset | None, *, trait: Space
) -> tuple[ValidationReport, str]:
    """Validate a dataset against the selected space trait specification.

    Parameters
    ----------
    ds : xr.Dataset | None
        Dataset to validate. ``None`` is only supported when checks are disabled
        (e.g. docs rendering mode via ``skip_all_checks``).
    trait : Space
        Selected space trait profile.

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

    This document defines trait-level requirements for spatial coordinates in MLWP datasets.
    The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
    "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
    interpreted as described in RFC 2119.

    ## 2. Scope

    This specification applies to datasets validated with the `space={trait.value}`
    profile.

    ## 3. Structural Requirements

    ### 3.1 Accepted Dimension Variants

    """
    if trait == Space.GRID:
        spec_text += """
    - The dataset MUST match one of the accepted dimension variants for this profile:
      `[{'xc', 'yc'}, {'grid_index'}, {'longitude', 'latitude'}]`.
    """
        report += check_dim_variants(
            ds,
            axis="space",
            variants=[
                {"xc", "yc"},
                {"grid_index"},
                {"longitude", "latitude"},
            ],
        )
    elif trait == Space.POINT:
        spec_text += """
    - The dataset MUST include the `point_index` dimension for the spatial axis.
    - This profile enforces the single spatial dimension variant `{'point_index'}`.
    """
        report += check_dim_variants(ds, axis="space", variants=[{"point_index"}])
    else:
        raise NotImplementedError(f"Unsupported spatial trait: {trait!r}")

    spec_text += """
    ### 3.2 Required Coordinates

    - The dataset MUST include required coordinates for this profile:
      `['latitude', 'longitude']`.
    """
    report += check_required_coords(
        ds, axis="space", required_coords={"longitude", "latitude"}
    )

    spec_text += """
    ### 3.3 Optional Coordinates

    """
    if trait == Space.GRID:
        spec_text += """
    - The dataset MAY include optional coordinates for this profile:
      `['xc', 'yc']`.
    """
    elif trait == Space.POINT:
        spec_text += """
    - The dataset MAY include optional coordinates for this profile:
      `['code', 'country', 'elevation', 'name']`.
    """
    else:
        raise NotImplementedError(f"Unsupported spatial trait: {trait!r}")

    spec_text += """
    ### 3.4 Optional Dimensions

    """
    if trait == Space.GRID:
        spec_text += """
    - The dataset MAY include optional dimensions for this profile:
      `['member']`.
    """
    elif trait == Space.POINT:
        spec_text += """
    - The dataset MAY include optional dimensions for this profile:
      `[]`.
    """
    else:
        raise NotImplementedError(f"Unsupported spatial trait: {trait!r}")

    spec_text += """
    ## 4. Coordinate Metadata Requirements

    - Longitude/latitude coordinates MUST carry CF-compatible `standard_name` and angular units.
    - If projected coordinates are present (`xc`, `yc`), they MUST expose projection coordinate metadata.
    """

    report += check_space_coordinate_metadata(ds, trait=trait)

    return report, textwrap.dedent(spec_text)
