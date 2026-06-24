"""MLWP data specifications package."""

from importlib.metadata import version

from .api import validate_dataset

__all__ = ["__version__", "validate_dataset"]
__version__ = version("mlwp-data-specs")
