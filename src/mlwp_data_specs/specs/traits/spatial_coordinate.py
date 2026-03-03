"""Executable specification for spatial-coordinate traits."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
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


@dataclass
class PropertySpec:
    """Structural requirements for a space trait profile."""

    dim_variants: list[set[str]] = field(default_factory=list)
    required_coords: set[str] = field(default_factory=set)
    optional_dims: set[str] = field(default_factory=set)
    optional_coords: set[str] = field(default_factory=set)


SPACE_SPECS: dict[str, PropertySpec] = {
    "grid": PropertySpec(
        dim_variants=[
            {"xc", "yc"},
            {"grid_index"},
            {"longitude", "latitude"},
        ],
        required_coords={"longitude", "latitude"},
        optional_coords={"xc", "yc"},
        optional_dims={"member"},
    ),
    "point": PropertySpec(
        dim_variants=[{"point_index"}],
        required_coords={"longitude", "latitude"},
        optional_coords={"code", "elevation", "name", "country"},
    ),
}


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
    if trait == Space.GRID:
        structural_requirements = """
    - Accepted dimension variants are: `{'xc', 'yc'}` OR `{'grid_index'}` OR `{'longitude', 'latitude'}`.
    - Required coordinates are: `longitude`, `latitude`.
    - Optional projected coordinates are: `xc`, `yc`.
    """
    else:
        structural_requirements = """
    - Accepted dimension variant is: `{'point_index'}`.
    - Required coordinates are: `longitude`, `latitude`.
    - Optional point metadata coordinates are: `code`, `elevation`, `name`, `country`.
    """

    spec_text = f"""
    ---
    trait: {IDENTIFIER}
    profile: {trait.value}
    version: {VERSION}
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

    {structural_requirements}
    """

    spec = SPACE_SPECS[trait.value]
    report += check_dim_variants(ds, axis="space", variants=spec.dim_variants)
    report += check_required_coords(
        ds, axis="space", required_coords=spec.required_coords
    )

    spec_text += """
    ## 4. Coordinate Metadata Requirements

    - Longitude/latitude coordinates MUST carry CF-compatible `standard_name` and angular units.
    - If projected coordinates are present (`xc`, `yc`), they MUST expose projection coordinate metadata.
    """

    report += check_space_coordinate_metadata(ds, trait=trait)

    return report, textwrap.dedent(spec_text)
