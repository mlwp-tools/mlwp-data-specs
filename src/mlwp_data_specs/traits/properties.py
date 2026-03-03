"""Trait definitions adapted from mxalign properties."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Space(str, Enum):
    """Supported spatial trait profiles."""

    GRID = "grid"
    POINT = "point"


class Time(str, Enum):
    """Supported temporal trait profiles."""

    FORECAST = "forecast"
    OBSERVATION = "observation"


class Uncertainty(str, Enum):
    """Supported uncertainty trait profiles."""

    DETERMINISTIC = "deterministic"
    ENSEMBLE = "ensemble"
    QUANTILE = "quantile"


@dataclass(frozen=True)
class TraitSelection:
    """Selected trait profiles for a validation run."""

    space: Space | None = None
    time: Time | None = None
    uncertainty: Uncertainty | None = None
