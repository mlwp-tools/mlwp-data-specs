#!/usr/bin/env python3
"""Generate docs pages from inline trait specifications."""

from __future__ import annotations

from pathlib import Path

from mlwp_data_specs import __version__
from mlwp_data_specs.traits.properties import Space, Time, Uncertainty
from mlwp_data_specs.traits.reporting import skip_all_checks
from mlwp_data_specs.specs.traits.spatial_coordinate import validate_dataset as validate_space
from mlwp_data_specs.specs.traits.time_coordinate import validate_dataset as validate_time
from mlwp_data_specs.specs.traits.uncertainty import validate_dataset as validate_uncertainty

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
    grouped_pages: dict[str, list[tuple[str, str]]] = {
        "space": [],
        "time": [],
        "uncertainty": [],
    }
    for name in page_names:
        if name.startswith("space_"):
            grouped_pages["space"].append((name, name.removeprefix("space_")))
        elif name.startswith("time_"):
            grouped_pages["time"].append((name, name.removeprefix("time_")))
        elif name.startswith("uncertainty_"):
            grouped_pages["uncertainty"].append((name, name.removeprefix("uncertainty_")))

    lines = [
        "# MLWP Trait Specifications",
        "",
        f"Generated from inline executable specs in `mlwp-data-specs` {__version__}.",
        "",
        "## Requirements",
        "",
        "- The validator checks selected dataset traits: `time`, `space`, `uncertainty`.",
        "- Checks include structural constraints and metadata constraints.",
        "- Trait specs remain executable and are rendered as documentation.",
        "",
        "## Interfaces",
        "",
        "Both interfaces are expected:",
        "",
        "1. Python API via `check_dataset(ds, time=..., space=..., uncertainty=...)`.",
        "2. CLI via `mlwp.validate_trait` for local/remote validation and CI usage.",
        "",
        "## Specs",
        "",
    ]
    for trait_type in ["space", "time", "uncertainty"]:
        lines.append(f"- {trait_type.capitalize()}")
        for page_name, profile in sorted(grouped_pages[trait_type], key=lambda x: x[1]):
            lines.append(f"    - [{profile}](traits/{page_name}.md)")

    (DOCS_DIR / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _usage_examples_for_page(page_name: str) -> str:
    """Return docs-only usage examples for a generated trait page.

    Parameters
    ----------
    page_name : str
        Generated page base name (for example ``space_grid``).

    Returns
    -------
    str
        Markdown section with CLI and Python examples for the page profile.
    """
    trait, profile = page_name.split("_", 1)
    cli_flag = trait
    api_kwarg = trait

    return (
        "## 5. How To Run This Trait Profile (Docs)\n\n"
        "Run with `uvx` from release on [pypi.org](https://pypi.org/):\n\n"
        "```bash\n"
        f"uvx --with mlwp-data-specs mlwp.validate_trait <DATASET_PATH_OR_URL> --{cli_flag} {profile}\n"
        "```\n\n"
        "> Warning: `mlwp-data-specs` is not published on PyPI yet, so this command is\n"
        "> included for future release usage.\n\n"
        "Run directly from GitHub source:\n\n"
        "```bash\n"
        f'uvx --from "git+https://github.com/leifdenby/mlwp-data-specs" mlwp.validate_trait <DATASET_PATH_OR_URL> --{cli_flag} {profile}\n'
        "```\n\n"
        "Python API:\n\n"
        "```python\n"
        "from mlwp_data_specs import check_dataset\n\n"
        f'report = check_dataset(ds, {api_kwarg}="{profile}")\n'
        "```\n"
    )


def _render_trait_page(page_name: str, content: str) -> str:
    """Render one trait page with docs-only additions.

    Parameters
    ----------
    page_name : str
        Generated page base name.
    content : str
        Base inline spec markdown from the validator module.

    Returns
    -------
    str
        Markdown page content including docs-only usage examples.
    """
    return content.strip() + "\n\n" + _usage_examples_for_page(page_name) + "\n"


def main() -> None:
    """Generate all trait markdown docs under ``docs/traits``."""
    TRAITS_DIR.mkdir(parents=True, exist_ok=True)
    pages = _render_specs()

    for name, content in pages.items():
        rendered = _render_trait_page(name, content)
        (TRAITS_DIR / f"{name}.md").write_text(rendered, encoding="utf-8")

    _write_index(sorted(pages.keys()))


if __name__ == "__main__":
    main()
