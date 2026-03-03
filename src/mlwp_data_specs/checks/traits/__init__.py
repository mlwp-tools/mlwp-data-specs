"""Trait-level structural checks."""

from .space import check_space_trait_structure
from .time import check_time_trait_structure
from .uncertainty import check_uncertainty_trait_structure

__all__ = [
    "check_space_trait_structure",
    "check_time_trait_structure",
    "check_uncertainty_trait_structure",
]
