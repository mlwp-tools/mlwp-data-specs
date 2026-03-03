#!/usr/bin/env python3
"""Generate docs pages from inline trait specifications."""

from __future__ import annotations

import re
from pathlib import Path

from mlwp_data_specs import __version__
from mlwp_data_specs.specs.reporting import skip_all_checks
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

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
TRAITS_DIR = DOCS_DIR / "traits"
REPO_URL = "https://github.com/leifdenby/mlwp-data-specs"
DEFAULT_BRANCH = "main"


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
        _, pages["uncertainty_ensemble"] = validate_uncertainty(
            None, trait=Uncertainty.ENSEMBLE
        )
        _, pages["uncertainty_quantile"] = validate_uncertainty(
            None, trait=Uncertainty.QUANTILE
        )

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
            grouped_pages["uncertainty"].append(
                (name, name.removeprefix("uncertainty_"))
            )

    lines = [
        "# MLWP Trait Specifications",
        "",
        f"Generated from inline executable specs in `mlwp-data-specs` {__version__}.",
        "",
        "## Interfaces",
        "",
        "Both interfaces are expected:",
        "",
        "1. Python API via `validate_dataset(ds, time=..., space=..., uncertainty=...)`.",
        "2. CLI via `mlwp.validate_dataset_traits` for local/remote validation and CI usage.",
        "",
        "## Specs",
        "",
    ]
    for trait_type in ["space", "time", "uncertainty"]:
        lines.append(f"- {trait_type.capitalize()}")
        for page_name, profile in sorted(grouped_pages[trait_type], key=lambda x: x[1]):
            lines.append(f"    - [{profile}](traits/{page_name}.md)")

    (DOCS_DIR / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _extract_frontmatter(spec_text: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from a spec markdown string.

    Parameters
    ----------
    spec_text : str
        Raw spec markdown including optional frontmatter.

    Returns
    -------
    tuple[dict[str, str], str]
        Parsed frontmatter key/value map and markdown body without frontmatter.
    """
    text = spec_text.strip()
    if not text.startswith("---"):
        return {}, text

    match = re.match(r"---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return {}, text

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    body = text[match.end() :].lstrip()
    return frontmatter, body


def _source_path_for_trait(trait: str) -> str:
    """Map trait axis name to source module path.

    Parameters
    ----------
    trait : str
        Trait axis name.

    Returns
    -------
    str
        Relative repository path for the trait spec module.
    """
    mapping = {
        "space": "src/mlwp_data_specs/specs/traits/spatial_coordinate.py",
        "spatial_coordinate": "src/mlwp_data_specs/specs/traits/spatial_coordinate.py",
        "time": "src/mlwp_data_specs/specs/traits/time_coordinate.py",
        "time_coordinate": "src/mlwp_data_specs/specs/traits/time_coordinate.py",
        "uncertainty": "src/mlwp_data_specs/specs/traits/uncertainty.py",
    }
    return mapping[trait]


def _usage_block_for_page(page_name: str) -> str:
    """Return docs-only usage instructions for a generated trait page.

    Parameters
    ----------
    page_name : str
        Generated page base name (for example ``space_grid``).

    Returns
    -------
    str
        Markdown usage instructions.
    """
    trait, profile = page_name.split("_", 1)

    return (
        "Run with `uvx` from release on [pypi.org](https://pypi.org/):\n\n"
        "```bash\n"
        f"uvx --with mlwp-data-specs mlwp.validate_dataset_traits <DATASET_PATH_OR_URL> --{trait} {profile}\n"
        "```\n\n"
        "> Warning: `mlwp-data-specs` is not published on PyPI yet, so this command is\n"
        "> included for future release usage.\n\n"
        "Run directly from GitHub source:\n\n"
        "```bash\n"
        f'uvx --from "git+https://github.com/leifdenby/mlwp-data-specs" mlwp.validate_dataset_traits <DATASET_PATH_OR_URL> --{trait} {profile}\n'
        "```\n\n"
        "Python API:\n\n"
        "```python\n"
        "from mlwp_data_specs import validate_dataset\n\n"
        f'report = validate_dataset(ds, {trait}="{profile}")\n'
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
    frontmatter, body = _extract_frontmatter(content)
    trait = frontmatter.get("trait", page_name.split("_", 1)[0])
    profile = frontmatter.get("profile", page_name.split("_", 1)[1])
    title = f"{trait.replace('_', ' ').title()} ({profile})"
    source_path = _source_path_for_trait(trait)
    source_url = f"{REPO_URL}/blob/{DEFAULT_BRANCH}/{source_path}"

    frontmatter_lines = [f"{k}: {v}" for k, v in sorted(frontmatter.items())]
    frontmatter_block = "\n".join(frontmatter_lines)
    usage = _usage_block_for_page(page_name).strip()

    parts = [
        f"# {title}",
        "",
    ]
    if frontmatter_block:
        parts.extend(
            [
                "```yaml",
                frontmatter_block,
                "```",
                "",
            ]
        )
    parts.extend(
        [
            f"[View spec source on GitHub]({source_url})",
            "",
            usage,
            "",
            "---",
            "",
            body.strip(),
            "",
        ]
    )
    return "\n".join(parts)


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
