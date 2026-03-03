#!/usr/bin/env python3
"""Generate docs pages from inline trait specifications."""

from __future__ import annotations

from pathlib import Path

from mlwp_data_specs import __version__
from mlwp_data_specs.traits.properties import Space, Time, Uncertainty
from mlwp_data_specs.traits.reporting import skip_all_checks
from mlwp_data_specs.traits.spatial_coordinate import validate_dataset as validate_space
from mlwp_data_specs.traits.time_coordinate import validate_dataset as validate_time
from mlwp_data_specs.traits.uncertainty import validate_dataset as validate_uncertainty

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
TRAITS_DIR = DOCS_DIR / "traits"


def _render_specs() -> dict[str, str]:
    """Render markdown specs for all trait/profile combinations.

    Returns
    -------
    dict[str, str]
        Mapping of output page name to markdown content.
    """
    pages: dict[str, str] = {}

    with skip_all_checks():
        _, pages["space_grid"] = validate_space(None, trait=Space.GRID)
        _, pages["space_point"] = validate_space(None, trait=Space.POINT)
        _, pages["time_forecast"] = validate_time(None, trait=Time.FORECAST)
        _, pages["time_observation"] = validate_time(None, trait=Time.OBSERVATION)
        _, pages["uncertainty_deterministic"] = validate_uncertainty(
            None, trait=Uncertainty.DETERMINISTIC
        )
        _, pages["uncertainty_ensemble"] = validate_uncertainty(None, trait=Uncertainty.ENSEMBLE)
        _, pages["uncertainty_quantile"] = validate_uncertainty(None, trait=Uncertainty.QUANTILE)

    return pages


def _write_index(page_names: list[str]) -> None:
    """Write the docs index page linking all generated trait pages.

    Parameters
    ----------
    page_names : list[str]
        Generated page base names (without extension).
    """
    lines = [
        "# MLWP Trait Specifications",
        "",
        f"Generated from inline executable specs in `mlwp-data-specs` {__version__}.",
        "",
        "## Available Spec Pages",
        "",
    ]
    for name in page_names:
        lines.append(f"- [{name.replace('_', ' ')}](traits/{name}.md)")

    (DOCS_DIR / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Generate all trait markdown docs under ``docs/traits``."""
    TRAITS_DIR.mkdir(parents=True, exist_ok=True)
    pages = _render_specs()

    for name, content in pages.items():
        (TRAITS_DIR / f"{name}.md").write_text(content.strip() + "\n", encoding="utf-8")

    _write_index(sorted(pages.keys()))


if __name__ == "__main__":
    main()
