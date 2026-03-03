"""Public Python API for trait-based dataset validation."""

from __future__ import annotations

from enum import Enum
from typing import TypeVar

import xarray as xr

from mlwp_data_specs.specs.traits.spatial_coordinate import (
    validate_dataset as validate_space,
)
from mlwp_data_specs.specs.traits.time_coordinate import (
    validate_dataset as validate_time,
)
from mlwp_data_specs.specs.traits.uncertainty import (
    validate_dataset as validate_uncertainty,
)
from mlwp_data_specs.traits.properties import Space, Time, Uncertainty
from mlwp_data_specs.traits.reporting import ValidationReport

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

    time_trait = _coerce_enum(time, Time, "time")
    space_trait = _coerce_enum(space, Space, "space")
    uncertainty_trait = _coerce_enum(uncertainty_value, Uncertainty, "uncertainty")

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
