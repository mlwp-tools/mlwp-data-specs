"""Public Python API for trait-based dataset validation."""

from __future__ import annotations

from enum import Enum
from typing import TypeVar

import xarray as xr
from loguru import logger

from mlwp_data_specs.specs.reporting import ValidationReport
from mlwp_data_specs.specs.traits.spatial_coordinate import (
    Space,
)
from mlwp_data_specs.specs.traits.spatial_coordinate import (
    validate_dataset as validate_space,
)
from mlwp_data_specs.specs.traits.time_coordinate import (
    Time,
)
from mlwp_data_specs.specs.traits.time_coordinate import (
    validate_dataset as validate_time,
)
from mlwp_data_specs.specs.traits.uncertainty import (
    Uncertainty,
)
from mlwp_data_specs.specs.traits.uncertainty import (
    validate_dataset as validate_uncertainty,
)

_TRAIT_ATTR_FORMAT = "mlwp_{}_trait"

TIME_TRAIT_ATTR = _TRAIT_ATTR_FORMAT.format("time")
SPACE_TRAIT_ATTR = _TRAIT_ATTR_FORMAT.format("space")
UNCERTAINTY_TRAIT_ATTR = _TRAIT_ATTR_FORMAT.format("uncertainty")

EnumType = TypeVar("EnumType", bound=Enum)


def _coerce_enum(
    value: EnumType | str | None, enum_cls: type[EnumType], name: str
) -> EnumType | None:
    """Coerce user input into an enum value.

    Parameters
    ----------
    value : EnumType | str | None
        Input enum value or raw string.
    enum_cls : type[EnumType]
        Target enum class.
    name : str
        Argument name used in error messages.

    Returns
    -------
    EnumType | None
        Parsed enum value or ``None``.

    Raises
    ------
    ValueError
        Raised when a string value is not one of the supported enum values.
    """
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError as exc:
        choices = ", ".join(item.value for item in enum_cls)
        raise ValueError(
            f"Invalid value for '{name}': {value!r}. Expected one of: {choices}"
        ) from exc


def _resolve_trait(
    ds: xr.Dataset,
    arg_value: EnumType | str | None,
    enum_cls: type[EnumType],
) -> EnumType | None:
    """Resolve a trait value from argument or dataset attributes.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset.
    arg_value : EnumType | str | None
        The trait value passed as an argument.
    enum_cls : type[EnumType]
        The enum class for the trait.

    Returns
    -------
    EnumType | None
        The resolved trait value or ``None``.
    """
    trait_name = enum_cls.__name__.lower()
    attr_name = _TRAIT_ATTR_FORMAT.format(trait_name)

    arg_trait = _coerce_enum(arg_value, enum_cls, trait_name)
    attr_value = ds.attrs.get(attr_name)

    if attr_value is None:
        return arg_trait

    try:
        attr_trait = _coerce_enum(attr_value, enum_cls, f"attribute {attr_name}")
    except ValueError as exc:
        logger.warning(f"Invalid trait value in attribute '{attr_name}': {exc}")
        return arg_trait

    if arg_trait is not None and arg_trait != attr_trait:
        logger.warning(
            f"Provided {trait_name} trait '{arg_trait.value}' differs from "
            f"dataset attribute '{attr_name}' ('{attr_trait.value}'). "
            f"Using provided trait value '{arg_trait.value}'."
        )
        return arg_trait

    return arg_trait if arg_trait is not None else attr_trait


def validate_dataset(
    ds: xr.Dataset,
    *,
    time: Time | str | None = None,
    space: Space | str | None = None,
    uncertainty: Uncertainty | str | None = None,
    uncertaity: Uncertainty | str | None = None,
) -> ValidationReport:
    """Validate a dataset against selected trait specifications.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to validate.
    time : Time | str | None, optional
        Time trait profile (for example ``"forecast"`` or ``"observation"``).
    space : Space | str | None, optional
        Space trait profile (for example ``"grid"`` or ``"point"``).
    uncertainty : Uncertainty | str | None, optional
        Uncertainty trait profile (for example ``"deterministic"``,
        ``"ensemble"``, or ``"quantile"``).
    uncertaity : Uncertainty | str | None, optional
        Backward-compatible alias for ``uncertainty`` (spelling preserved).

    Returns
    -------
    ValidationReport
        Combined report across selected trait checks.

    Raises
    ------
    ValueError
        Raised when no traits are selected or when invalid trait values are provided.
    """
    if uncertainty is not None and uncertaity is not None:
        raise ValueError("Provide only one of 'uncertainty' or 'uncertaity', not both")

    uncertainty_value = uncertainty if uncertainty is not None else uncertaity

    time_trait = _resolve_trait(ds, time, Time)
    space_trait = _resolve_trait(ds, space, Space)
    uncertainty_trait = _resolve_trait(ds, uncertainty_value, Uncertainty)

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

    return report
