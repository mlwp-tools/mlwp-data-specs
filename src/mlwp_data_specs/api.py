"""Public Python API for trait-based dataset validation."""

from __future__ import annotations

import xarray as xr
from loguru import logger

from mlwp_data_specs.checks.global_attributes.traits import (
    TRAIT_ATTR_FORMAT,
    check_trait_attribute,
)
from mlwp_data_specs.specs.reporting import ValidationReport
from mlwp_data_specs.specs.traits.spatial_coordinate import (
    SPACE_TRAIT_ATTR,
)
from mlwp_data_specs.specs.traits.spatial_coordinate import (
    validate_dataset as validate_space,
)
from mlwp_data_specs.specs.traits.time_coordinate import (
    TIME_TRAIT_ATTR,
)
from mlwp_data_specs.specs.traits.time_coordinate import (
    validate_dataset as validate_time,
)
from mlwp_data_specs.specs.traits.uncertainty import (
    UNCERTAINTY_TRAIT_ATTR,
)
from mlwp_data_specs.specs.traits.uncertainty import (
    validate_dataset as validate_uncertainty,
)
from mlwp_data_specs.trait_profiles import Space, StrEnumLike, Time, Uncertainty

__all__ = [
    "SPACE_TRAIT_ATTR",
    "TIME_TRAIT_ATTR",
    "UNCERTAINTY_TRAIT_ATTR",
    "Space",
    "Time",
    "Uncertainty",
    "validate_dataset",
]


def _check_trait_value(
    value: str | None, profiles_cls: type[StrEnumLike], name: str
) -> str | None:
    """Check that a trait value is one of the supported profiles.

    Parameters
    ----------
    value : str | None
        Trait profile value, or ``None`` if not given.
    profiles_cls : type[StrEnumLike]
        Class listing the supported profiles for the trait axis.
    name : str
        Argument name used in error messages.

    Returns
    -------
    str | None
        The unchanged value.

    Raises
    ------
    ValueError
        Raised when ``value`` is not one of the supported profiles.
    """
    if value is not None and value not in profiles_cls:
        choices = ", ".join(profiles_cls)
        raise ValueError(
            f"Invalid value for '{name}': {value!r}. Expected one of: {choices}"
        )
    return value


def _resolve_trait(
    ds: xr.Dataset,
    arg_value: str | None,
    profiles_cls: type[StrEnumLike],
) -> str | None:
    """Resolve a trait value from argument or dataset attributes.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset.
    arg_value : str | None
        The trait value passed as an argument.
    profiles_cls : type[StrEnumLike]
        Class listing the supported profiles for the trait axis.

    Returns
    -------
    str | None
        The resolved trait value or ``None``.
    """
    trait_name = profiles_cls.__name__.lower()
    attr_name = TRAIT_ATTR_FORMAT.format(trait_name)

    arg_trait = _check_trait_value(arg_value, profiles_cls, trait_name)
    attr_value = ds.attrs.get(attr_name)

    if attr_value is None:
        return arg_trait

    try:
        attr_trait = _check_trait_value(
            attr_value, profiles_cls, f"attribute {attr_name}"
        )
    except ValueError as exc:
        logger.warning(f"Invalid trait value in attribute '{attr_name}': {exc}")
        return arg_trait

    if arg_trait is not None and arg_trait != attr_trait:
        logger.warning(
            f"Provided {trait_name} trait '{arg_trait}' differs from "
            f"dataset attribute '{attr_name}' ('{attr_trait}'). "
            f"Using provided trait value '{arg_trait}'."
        )
        return arg_trait

    return arg_trait if arg_trait is not None else attr_trait


def validate_dataset(
    ds: xr.Dataset,
    *,
    time: str | None = None,
    space: str | None = None,
    uncertainty: str | None = None,
) -> ValidationReport:
    """Validate a dataset against selected trait specifications.

    If a trait is not explicitly provided as an argument, this function
    will attempt to resolve it from the dataset's attributes (e.g.,
    ``mlwp_time_trait``, ``mlwp_space_trait``, ``mlwp_uncertainty_trait``).
    If both are provided and differ, the argument takes precedence.

    A trait attribute that is present is always checked, even for traits that
    are not validated, so an invalid value is reported as a failure.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to validate.
    time : str | None, optional
        Time trait profile, one of the `Time` members (for example
        ``Time.FORECAST``).
    space : str | None, optional
        Space trait profile, one of the `Space` members (for example
        ``Space.GRID``).
    uncertainty : str | None, optional
        Uncertainty trait profile, one of the `Uncertainty` members (for
        example ``Uncertainty.ENSEMBLE``).

    Returns
    -------
    ValidationReport
        Combined report across selected trait checks.

    Raises
    ------
    ValueError
        Raised when no traits are selected or when invalid trait values are provided.
    """
    time_trait = _resolve_trait(ds, time, Time)
    space_trait = _resolve_trait(ds, space, Space)
    uncertainty_trait = _resolve_trait(ds, uncertainty, Uncertainty)

    if not any([time_trait, space_trait, uncertainty_trait]):
        raise ValueError("At least one trait must be selected")

    report = ValidationReport()

    if time_trait is not None:
        trait_report, _ = validate_time(ds, trait=time_trait)
        report += trait_report

    if space_trait is not None:
        trait_report, _ = validate_space(ds, trait=space_trait)
        report += trait_report

    if uncertainty_trait is not None:
        trait_report, _ = validate_uncertainty(ds, trait=uncertainty_trait)
        report += trait_report

    # trait specs check their own attribute; check the rest for validity only
    unvalidated = [
        ("time", Time, time_trait, TIME_TRAIT_ATTR),
        ("space", Space, space_trait, SPACE_TRAIT_ATTR),
        ("uncertainty", Uncertainty, uncertainty_trait, UNCERTAINTY_TRAIT_ATTR),
    ]
    for trait_axis, trait_cls, trait, attr_name in unvalidated:
        if trait is None and attr_name in ds.attrs:
            report += check_trait_attribute(
                ds, trait_axis=trait_axis, trait_cls=trait_cls
            )

    return report
