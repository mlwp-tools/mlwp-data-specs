"""Helpers for importing and applying optional dataset loader hooks."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import xarray as xr

LoaderHooks = dict[str, Any]


def _load_module(loader: str) -> ModuleType:
    """Import a loader module from a Python file or module path.

    Parameters
    ----------
    loader : str
        Loader reference. A value ending in ``.py`` is treated as a file path.
        A value containing ``.`` is treated as a Python module path.

    Returns
    -------
    types.ModuleType
        Imported module object.

    Raises
    ------
    ValueError
        If the loader reference cannot be resolved.
    """
    if loader.endswith(".py"):
        path = Path(loader)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not import loader module from file: {loader}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    if "." in loader:
        return importlib.import_module(loader)
    raise ValueError(
        "Loader must be a Python file path ending in .py or a Python module path"
    )


def import_loader_hooks(loader: str) -> LoaderHooks:
    """Import optional loader hooks from a Python file or module.

    Parameters
    ----------
    loader : str
        Loader reference. A value ending in ``.py`` is treated as a file path.
        A value containing ``.`` is treated as a Python module path.

    Returns
    -------
    LoaderHooks
        Mapping with the loader hooks explicitly defined by the imported module.
    """
    module = _load_module(loader)
    hooks: LoaderHooks = {}
    variable_hooks = {
        "open_kwargs": ("OPEN_KWARGS",),
        "concat_dim": ("CONCAT_DIM",),
        "valid_time_profiles": ("valid_time_profiles",),
        "valid_space_profiles": ("valid_space_profiles",),
        "valid_uncertainty_profiles": ("valid_uncertainty_profiles",),
    }
    function_hooks = ("preprocess", "postprocess")

    for hook_name, attr_names in variable_hooks.items():
        for attr_name in attr_names:
            if hasattr(module, attr_name):
                hooks[hook_name] = getattr(module, attr_name)
                break

    for name in function_hooks:
        if hasattr(module, name):
            hooks[name] = getattr(module, name)
    return hooks


def validate_loader_profiles(
    hooks: LoaderHooks,
    *,
    time: str | None = None,
    space: str | None = None,
    uncertainty: str | None = None,
) -> None:
    """Validate requested trait profiles against loader constraints.

    Parameters
    ----------
    hooks : LoaderHooks
        Loader hook mapping returned by :func:`import_loader_hooks`.
    time : str | None, optional
        Requested time profile.
    space : str | None, optional
        Requested space profile.
    uncertainty : str | None, optional
        Requested uncertainty profile.

    Raises
    ------
    ValueError
        If a requested trait profile is incompatible with the loader.
    """
    requested = {
        "time": (time, hooks.get("valid_time_profiles")),
        "space": (space, hooks.get("valid_space_profiles")),
        "uncertainty": (uncertainty, hooks.get("valid_uncertainty_profiles")),
    }
    for axis, (value, allowed) in requested.items():
        if value is None or allowed is None:
            continue
        if value not in allowed:
            choices = ", ".join(allowed)
            raise ValueError(
                f"Loader does not support {axis}={value!r}. Expected one of: {choices}"
            )


def open_with_loader(
    files: str | Sequence[str],
    *,
    hooks: LoaderHooks,
    storage_options: dict[str, Any] | None = None,
) -> xr.Dataset | xr.DataArray:
    """Open and normalize one or more datasets using loader hooks.

    Parameters
    ----------
    files : str | Sequence[str]
        One path or a sequence of paths to source datasets.
    hooks : LoaderHooks
        Loader hook mapping returned by :func:`import_loader_hooks`.
    storage_options : dict[str, Any] | None, optional
        Storage options forwarded to :func:`xarray.open_dataset`.

    Returns
    -------
    xr.Dataset | xr.DataArray
        Final object after preprocessing, combination, and postprocessing.

    Raises
    ------
    ValueError
        If multiple input paths are provided but the loader does not define
        ``concat_dim``.
    """
    paths = [files] if isinstance(files, str) else list(files)
    preprocess = hooks.get("preprocess", None)
    postprocess = hooks.get("postprocess", None)
    concat_dim = hooks.get("concat_dim", None)
    loader_open_kwargs = dict(hooks.get("open_kwargs", {}))

    parts = []
    for path in paths:
        part = xr.open_dataset(
            path,
            storage_options=storage_options,
            **loader_open_kwargs,
        )
        if preprocess is not None:
            part = preprocess(part)
        parts.append(part)

    if len(parts) > 1:
        if concat_dim is None:
            raise ValueError(
                "Loader must define 'concat_dim' when multiple dataset paths are provided"
            )
        combined = xr.concat(parts, dim=concat_dim)
    else:
        combined = parts[0]
    if postprocess is not None:
        combined = postprocess(combined)
    return combined
