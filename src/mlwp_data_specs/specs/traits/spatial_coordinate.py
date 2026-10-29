"""Executable specification for spatial-coordinate traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.coords.dimensions import check_dim_variants
from mlwp_data_specs.checks.coords.names import check_required_coords
from mlwp_data_specs.checks.coords.spatial import check_space_coordinate_metadata
from mlwp_data_specs.checks.global_attributes.traits import (
    TRAIT_ATTR_FORMAT,
    check_trait_attribute,
)
from mlwp_data_specs.specs.reporting import ValidationReport
from mlwp_data_specs.trait_profiles import Space

__all__ = ["IDENTIFIER", "SPACE_TRAIT_ATTR", "VERSION", "Space", "validate_dataset"]

VERSION = "0.1.1-draft"
IDENTIFIER = "spatial_coordinate"
SPACE_TRAIT_ATTR = TRAIT_ATTR_FORMAT.format("space")


def validate_dataset(
    ds: xr.Dataset | None, *, trait: str
) -> tuple[ValidationReport, str]:
    """Validate a dataset against the selected space trait specification.

    Parameters
    ----------
    ds : xr.Dataset | None
        Dataset to validate. ``None`` is only supported when checks are disabled
        (e.g. docs rendering mode via ``skip_all_checks``).
    trait : str
        Selected space trait profile, one of the `Space` members.

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

    This document defines trait-level requirements for spatial coordinates in MLWP datasets.
    The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
    "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
    interpreted as described in RFC 2119.

    ## 2. Scope

    This specification applies to datasets validated with the `space={trait}`
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
            trait_axis="space",
            variants=[
                {"xc", "yc"},
                {"grid_index"},
                {"longitude", "latitude"},
            ],
        )
    elif trait == Space.POINT:
        spec_text += """
    - The dataset MUST include the `point_index` dimension for the spatial trait axis.
    """
        report += check_dim_variants(ds, trait_axis="space", variants=[{"point_index"}])
    else:
        raise NotImplementedError(f"Unsupported spatial trait: {trait!r}")

    spec_text += """
    ### 3.2 Required Coordinates

    - The dataset MUST include the `latitude` and `longitude` coordinates.
    """
    report += check_required_coords(
        ds, trait_axis="space", required_coords={"longitude", "latitude"}
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

    allowed = ", ".join(f"`{profile}`" for profile in Space)
    spec_text += f"""
    ## 5. Global Attributes

    - The dataset MAY include the global attribute `{SPACE_TRAIT_ATTR}` to declare its
      spatial trait profile.
    - If present, `{SPACE_TRAIT_ATTR}` MUST be one of: {allowed}.
    - If present, `{SPACE_TRAIT_ATTR}` SHOULD equal `{trait}`, the profile being
      validated.
    - The requirement on the value of `{SPACE_TRAIT_ATTR}` applies to any dataset
      that carries the attribute, including datasets validated only against other
      traits.
    """
    report += check_trait_attribute(
        ds, trait_axis="space", trait_cls=Space, trait=trait
    )

    return report, textwrap.dedent(spec_text)
