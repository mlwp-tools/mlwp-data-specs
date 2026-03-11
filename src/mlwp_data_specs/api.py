"""Public Python API for trait-based dataset validation."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeVar

import xarray as xr

from mlwp_data_specs.loaders import (
    import_loader_hooks,
    open_with_loader,
    validate_loader_profiles,
)
from mlwp_data_specs.specs.reporting import ValidationReport
from mlwp_data_specs.specs.traits.spatial_coordinate import Space
from mlwp_data_specs.specs.traits.spatial_coordinate import (
    validate_dataset as validate_space,
)
from mlwp_data_specs.specs.traits.time_coordinate import Time
from mlwp_data_specs.specs.traits.time_coordinate import (
    validate_dataset as validate_time,
)
from mlwp_data_specs.specs.traits.uncertainty import Uncertainty
from mlwp_data_specs.specs.traits.uncertainty import (
    validate_dataset as validate_uncertainty,
)

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


def open_dataset(
    dataset_path: str | list[str],
    *,
    loader: str | None = None,
    time: Time | str | None = None,
    space: Space | str | None = None,
    uncertainty: Uncertainty | str | None = None,
    storage_options: dict[str, Any] | None = None,
) -> xr.Dataset | xr.DataArray:
    """Open a dataset directly or through an optional loader module.

    Parameters
    ----------
    dataset_path : str | list[str]
        Path or paths to dataset stores.
    loader : str | None, optional
        Loader module reference. A value ending in ``.py`` is treated as a file
        path. A value containing ``.`` is treated as a Python module path.
    time : Time | str | None, optional
        Optional time trait selector used to verify loader compatibility.
    space : Space | str | None, optional
        Optional space trait selector used to verify loader compatibility.
    uncertainty : Uncertainty | str | None, optional
        Optional uncertainty trait selector used to verify loader compatibility.
    storage_options : dict[str, Any] | None, optional
        Storage options forwarded to :func:`xarray.open_dataset`.

    Returns
    -------
    xr.Dataset | xr.DataArray
        Opened dataset-like object.
    """
    if loader is None:
        return xr.open_dataset(
            dataset_path,
            storage_options=storage_options,
        )

    hooks = import_loader_hooks(loader)
    validate_loader_profiles(
        hooks,
        time=_coerce_enum(time, Time, "time").value if time is not None else None,
        space=_coerce_enum(space, Space, "space").value if space is not None else None,
        uncertainty=(
            _coerce_enum(uncertainty, Uncertainty, "uncertainty").value
            if uncertainty is not None
            else None
        ),
    )
    return open_with_loader(
        dataset_path,
        hooks=hooks,
        storage_options=storage_options,
    )
