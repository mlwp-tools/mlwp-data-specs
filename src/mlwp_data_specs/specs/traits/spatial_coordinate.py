"""Executable specification for spatial-coordinate traits."""

from __future__ import annotations

import textwrap

import xarray as xr

from mlwp_data_specs.checks.metadata.coords import check_space_coordinate_metadata
from mlwp_data_specs.checks.traits.space import check_space_trait_structure
from mlwp_data_specs.traits.properties import Space
from mlwp_data_specs.traits.reporting import ValidationReport

VERSION = "0.1.0"
IDENTIFIER = "spatial_coordinate"


def validate_dataset(ds: xr.Dataset | None, *, trait: Space) -> tuple[ValidationReport, str]:
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

    ## 1. Scope

    This specification enforces spatial-coordinate trait conformance for gridded and point datasets.

    ## 2. Structural Requirements

    {structural_requirements}
    """

    report += check_space_trait_structure(ds, trait=trait)

    spec_text += """
    ## 3. Coordinate Metadata Requirements

    - Longitude/latitude coordinates MUST carry CF-compatible `standard_name` and angular units.
    - If projected coordinates are present (`xc`, `yc`), they MUST expose projection coordinate metadata.
    """

    report += check_space_coordinate_metadata(ds, trait=trait)

    return report, textwrap.dedent(spec_text)
