# Plan: Trait-Based Dataset Validator Package for `mlwp-data-specs`

## Goal
Create a Python package in this repository that validates datasets using:
- The **trait model and core validation behavior** already implemented in `mxalign` (time, space, uncertainty properties).
- The **inline Markdown spec + check-function execution pattern** used by `mlcast-dataset-validator`.
- A docs workflow that renders trait specs to HTML (via MkDocs or equivalent static docs pipeline).

This validator should enforce coordinate naming/metadata constraints (`name`, `standard_name`, units/attrs) and structural constraints for three traits:
1. time-coordinate
2. spatial-coordinate
3. uncertainty estimates

## Implementation Checklist

- [ ] Phase 0: Package baseline and dependency setup completed
- [ ] Phase 1: Reporting model (`Result`, `ValidationReport`, check registry) implemented
- [ ] Phase 2: `mxalign` trait semantics adapted (space/time/uncertainty structure checks)
- [ ] Phase 3: Coordinate metadata checks implemented (`standard_name`, units, axis/attrs)
- [ ] Phase 4: Inline trait spec modules implemented (time, space, uncertainty)
- [ ] Phase 5: CLI trait selectors implemented (`--space`, `--time`, `--uncertainty`)
- [ ] Phase 5: CLI listing commands implemented (`--list-space`, `--list-time`, `--list-uncertainty`)
- [ ] Phase 6: Trait docs generator implemented and HTML docs build configured
- [ ] Phase 7: Unit and CLI tests implemented
- [ ] Phase 7: Integration test against HARMONIE Zarr URL pattern implemented
- [ ] Definition of Done satisfied

---

## 1. Scope and Architecture Decisions

1. Package name: create a new package under this repo (e.g. `mlwp_data_specs`).
2. Validation model: trait-by-trait checks with composable reports (PASS/WARNING/FAIL), matching `mlcast_dataset_validator.specs.reporting.ValidationReport`.
3. Trait semantics source of truth: reuse `mxalign` property concepts (`Space`, `Time`, `Uncertainty`, variants/spec tables) and extend them with metadata checks (e.g. `standard_name`, `units`, optional attrs).
4. Spec style: each trait spec module defines:
- `VERSION`, `IDENTIFIER`
- `validate_trait(ds, ...) -> (ValidationReport, spec_markdown)`
- inline Markdown requirement blocks adjacent to check function calls.
5. CLI/docs behavior: mirror `mlcast-dataset-validator`:
- discover available spec modules dynamically
- run checks or print spec markdown
- generate docs pages from inline markdown and build static HTML.

---

## 2. Proposed Package Layout

```text
mlwp_data_specs/
  __init__.py
  checks/
    __init__.py
    traits/
      __init__.py
      time.py
      space.py
      uncertainty.py
    metadata/
      __init__.py
      coords.py            # standard_name, units, axis attrs checks
  traits/
    __init__.py
    reporting.py           # ValidationReport, Result, decorator/registry
    cli.py                 # generic trait validator CLI
    time_coordinate.py     # inline spec + validation composition
    spatial_coordinate.py  # inline spec + validation composition
    uncertainty.py         # inline spec + validation composition
docs/
  index.md
  traits/
  scripts/
    generate_trait_docs.py
tests/
  test_trait_time.py
  test_trait_space.py
  test_trait_uncertainty.py
  test_cli.py
```

---

## 3. Implementation Phases

## Phase 0: Baseline and dependency setup

1. Update `pyproject.toml` to define package metadata and entry points:
- `mlwp.validate_trait = mlwp_data_specs.traits.cli:main`
2. Add dependencies needed by existing behavior:
- runtime: `xarray`, `loguru`, `rich`, `packaging`
- docs: `mkdocs` (+ theme/plugins as needed)
- tests: `pytest`
3. Confirm import path works from repository root (`python -m ...` and CLI entry point).

Deliverable: installable package skeleton with a no-op CLI.

## Phase 1: Reporting and check registry foundation

1. Implement `traits/reporting.py` by adapting the `mlcast` model:
- `Result`
- `ValidationReport` (merge/add/summary/console output)
- `log_function_call` decorator and check registry for introspection/mock skipping.
2. Keep status vocabulary fixed (`PASS`, `WARNING`, `FAIL`).
3. Add helper to skip check execution when generating markdown-only docs.

Deliverable: stable reporting API used by all checks/spec modules.

## Phase 2: Reuse mxalign trait semantics

1. Introduce trait enums/data classes aligned with `mxalign.properties`:
- `Space`, `Time`, `Uncertainty`
- `PropertySpec` and spec tables for valid dim/coord variants.
2. Reuse/adapt validation helpers from `mxalign.properties.validation`:
- dim variant validation
- required coordinate presence
3. Replace `ValueError` raising with report entries so all failures are aggregated.

Deliverable: trait-structure checks equivalent to `mxalign`, surfaced through `ValidationReport`.

## Phase 3: Add coordinate metadata enforcement

1. Implement checks for coordinate metadata requirements:
- required coordinate names by trait variant
- `standard_name` correctness per coord
- `units` and optional `axis`/`long_name` expectations
2. Keep these checks isolated in `checks/metadata/coords.py`, called from trait modules.
3. Add requirement IDs/labels per check so markdown requirements map cleanly to output rows.

Deliverable: trait checks validate both structure and metadata.

## Phase 4: Trait spec modules with inline markdown

1. Build three trait spec modules:
- `time_coordinate.py`
- `spatial_coordinate.py`
- `uncertainty.py`
2. For each module:
- write frontmatter (`trait`, `version`, optional profile)
- append markdown requirement sections inline
- call check functions immediately after each requirement block
- return `(report, dedented_spec_markdown)`
3. Keep requirement ordering stable (used by docs/tests).

Deliverable: executable specifications for each trait.

## Phase 5: Generic CLI with optional trait selectors

1. Implement a single CLI in `traits/cli.py` that exposes optional trait args:
- `--space <space-trait-name>`
- `--time <time-trait-name>`
- `--uncertainty <uncertainty-trait-name>`
2. Validation behavior:
- run only the selected trait checks
- if multiple selectors are provided, run the union of selected trait checks
- if none are provided, either fail fast with usage guidance or run a documented default profile (decide and document explicitly)
3. CLI commands:
- `--list-space`, `--list-time`, `--list-uncertainty` to show allowed values
- `--print-spec-markdown` for selected trait(s) without dataset validation
3. Support storage options if needed (`xarray.open_zarr` options).
4. Exit code policy:
- non-zero on FAIL
- zero on PASS/WARNING only.

Deliverable: user-facing validator CLI that filters checks by selected traits.

## Phase 6: Trait docs rendering to HTML

1. Add `docs/scripts/generate_trait_docs.py`:
- discover trait modules
- call CLI/spec function in “skip checks” mode
- extract frontmatter/body
- emit `docs/traits/*.md` pages and docs index.
2. Configure docs build (`mkdocs.yml`) so HTML pages are generated from these files.
3. Ensure each page links to source module and command-line usage examples.

Deliverable: generated HTML spec documentation for all traits.

## Phase 7: Tests and CI

1. Unit tests:
- check-level pass/fail/warning cases per trait
- metadata enforcement (`standard_name`, units, missing attrs)
- report merge and CLI exit codes
2. Golden tests:
- `--print-spec-markdown` contains expected requirement headings and frontmatter keys.
3. Docs test:
- generation script runs cleanly and produces trait pages.
4. Add CI job stages:
- lint
- tests
- docs build.

Deliverable: confidence that validator behavior and rendered specs stay consistent.

---

## 4. Trait Requirement Matrix (initial draft)

1. `time-coordinate`
- Required dimensions/coords per mode (`valid_time` or `reference_time+lead_time`).
- Monotonicity and regularity rules (as applicable).
- Required metadata (`standard_name`, units, calendar where relevant).

2. `spatial-coordinate`
- Required coordinate pairs for grid/point representations.
- Accepted dim variants from `mxalign` (`xc/yc`, `longitude/latitude`, etc.).
- Required metadata (`standard_name`, units in degrees/meters, axis tags).

3. `uncertainty estimates`
- Deterministic: no uncertainty coord required.
- Ensemble: require `member` coordinate and valid indexing/attrs.
- Quantile: require `quantile` coordinate with valid bounds/units semantics.

---

## 5. Execution Order

1. Build reporting + adapted mxalign trait validation primitives.
2. Add metadata checks for coordinates.
3. Implement inline spec modules for the three traits.
4. Add CLI discovery and markdown printing.
5. Add docs generator and MkDocs wiring.
6. Add tests and CI.

This sequence keeps behavior testable early and prevents docs tooling from blocking core validation development.

---

## 6. Risks and Mitigations

1. Drift from upstream `mxalign` behavior.
- Mitigation: isolate adapted logic in one module and add regression tests copied from relevant `mxalign` cases.

2. Ambiguous metadata requirements across data sources.
- Mitigation: make strict requirements explicit in trait markdown and expose warnings for soft recommendations.

3. Spec/check mismatch over time.
- Mitigation: keep check invocation immediately under each markdown requirement block and add tests asserting requirement headings exist in printed specs.

4. Docs generation coupling to runtime dependencies.
- Mitigation: keep `skip_all_checks` mode that avoids opening datasets during spec rendering.

---

## 7. Definition of Done

1. `pip install -e .` installs a package with working CLI entry point.
2. Three trait specs exist as inline markdown + executable checks.
3. Validator enforces coordinate names and metadata (`standard_name`, units, etc.) across time/space/uncertainty traits.
4. HTML docs are generated from inline trait specs.
5. Tests cover trait checks, CLI behavior, and docs generation.
6. Add an integration test that validates a real forecast dataset from:
- `https://harmonie-zarr.s3.amazonaws.com/dini/control/<analysis_time>/single_levels.zarr`
- where `<analysis_time>` is computed at test runtime as:
  - `now_utc - 6 hours`
  - rounded down to the most recent 3-hour boundary (`00, 03, 06, ... , 21` UTC)
  - formatted as `%Y-%m-%dT%H0000Z` (example on 2026-03-03: `2026-03-03T090000Z` when `now_utc` is around `15:xxZ`)
- Expected trait selection/outcome for this dataset:
  - `--time forecast`
  - `--space grid`
  - uncertainty not selected (or deterministic default)
  - validation should pass for selected required checks (or, if external data variability is a concern, at minimum assert successful dataset open + trait detection + non-crashing validation run).
