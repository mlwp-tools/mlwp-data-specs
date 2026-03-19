# mlwp-data-specs

[![Spec Docs](https://img.shields.io/badge/spec%20docs-HTML-blue)](https://mlwp-tools.github.io/mlwp-data-specs/)
[![CI](https://github.com/mlwp-tools/mlwp-data-specs/actions/workflows/ci.yml/badge.svg)](https://github.com/mlwp-tools/mlwp-data-specs/actions/workflows/ci.yml)

Trait-based dataset validator for weather/climate datasets in Zarr format.

## Why this was made

To facilitate comparing forecasts from MLWP (Machine Learning Weather Prediction) models this validator implements  specifications so that a single well-defined format can be targeted. The motivation for this to allow different groups to share their forecasts in a common format so that general-purpose tooling can be built to examine these forecasts.
Specifically, the specifications is organized around **traits** (for example, how spatial location is represented) so that downstream tools like [`mxalign`](https://github.com/rmi-mlwp/mxalign) can deterministically map between datasets - or *align* datasets - that represent traits differently (for example, point-wise observations to gridded data, or the inverse mapping).

In summary, the goals of this project are to:

1. make trait-level dataset requirements explicit (`time`, `space`, `uncertainty`)
2. keep human-readable spec text and executable validation logic side-by-side
3. provide both CLI and Python APIs for local and remote Zarr validation
4. publish linkable HTML spec docs directly from the validator code

## When should you use this?

Use `mlwp-data-specs` when you need to verify that a dataset follows agreed MLWP trait conventions, regardless of whether you will run alignment operations.

The intended split is:

1. `mlwp-data-specs`: define and validate dataset structure/metadata contracts
2. `mxalign`: perform alignment/transformation operations on datasets

Typical use cases:

1. **Upstream reference dataset creation**: validate produced reference datasets (observations, NWP forecasts, etc.) at write-time (or just before writing) so they are known to satisfy the shared spec.
2. **Inference pipelines**: validate model output immediately at inference time before publishing/storing results.
3. **Pre-check before alignment**: validate first, then pass conformant datasets to `mxalign`.
4. **Downstream consumers that do not align**: visualization, QA, and analytics tools can enforce input structure without running alignment logic.
5. **CI quality gates**: fail fast when datasets drift from required trait conventions.

Concrete examples where this is useful include integrating checks in `nwp-forecast-zarr-creator` and validating upstream inference outputs (for example from ANNA / `neural-lam`) so downstream tooling, including `mxalign`, can consume them reliably.

## What is this?

`mlwp-data-specs` validates datasets across three orthogonal trait axes:

1. `time` (for example: `forecast`, `observation`)
2. `space` (for example: `grid`, `point`)
3. `uncertainty` (for example: `deterministic`, `ensemble`, `quantile`)

The validator enforces both structural requirements (dimensions/coordinates) and metadata requirements (`standard_name`, `units`, etc.).

## How specifications are implemented

- Executable trait specs are defined in `src/mlwp_data_specs/specs/traits/`.
- Each spec module contains inline markdown requirements plus adjacent check function calls.
- Rendered docs pages are generated from those inline specs with `docs/scripts/generate_trait_docs.py`.

## Code layout

The repository is organized so spec text, checks, and interfaces are separated but composable:

```text
src/mlwp_data_specs/
├── api.py                         # High-level Python API (validate_dataset)
├── specs/
│   ├── cli.py                     # CLI entry point (mlwp.validate_dataset_traits)
│   ├── reporting.py               # ValidationReport and check registry helpers
│   └── traits/
│       ├── spatial_coordinate.py  # Space trait enum + specs + validation wiring
│       ├── time_coordinate.py     # Time trait enum + specs + validation wiring
│       └── uncertainty.py         # Uncertainty trait enum + specs + validation wiring
├── checks/
│   ├── traits/
│   │   └── _common.py             # Shared structural check primitives
│   └── metadata/
│       └── coords.py              # standard_name/units/etc checks
```

## Requirements

- The validator MUST check datasets against selected trait specs (`time`, `space`, `uncertainty`).
- Checks MUST cover both structural constraints (dims/coords) and metadata constraints (`standard_name`, `units`, etc.).
- Specs MUST remain executable and renderable as documentation.

## Interfaces

The validator is expected to provide both interfaces:

1. Python API: programmatic validation via `validate_dataset(ds, time=..., space=..., uncertainty=...)`.
2. CLI: command-line validation via `mlwp.validate_dataset_traits` for local/remote datasets and CI usage.

## CLI usage

Install locally:

```bash
uv sync
```

Run validation for selected traits:

```bash
uv run mlwp.validate_dataset_traits <DATASET_PATH_OR_URL> --time forecast --space grid --uncertainty deterministic
```

Examples:

```bash
# Validate a local Zarr dataset
uv run mlwp.validate_dataset_traits /path/to/dataset.zarr --time forecast --space grid

# Validate a remote S3 dataset with anonymous access
uv run mlwp.validate_dataset_traits s3://bucket/dataset.zarr --time observation --space point --s3-anon

# List available trait values
uv run mlwp.validate_dataset_traits --list-time
uv run mlwp.validate_dataset_traits --list-space
uv run mlwp.validate_dataset_traits --list-uncertainty
```

Print inline markdown spec text without running validation:

```bash
uv run mlwp.validate_dataset_traits --time forecast --print-spec-markdown
```

## Python API usage

Use the high-level API:

```python
import xarray as xr
from mlwp_data_specs import validate_dataset

# Load dataset from local path or remote store
ds = xr.open_zarr("/path/to/dataset.zarr")

report = validate_dataset(
    ds,
    time="forecast",
    space="grid",
    uncertainty="deterministic",
)

report.console_print()

if report.has_fails():
    raise SystemExit("Dataset validation failed")
```

The API also accepts the requested alias spelling:

```python
report = validate_dataset(ds, time="forecast", space="grid", uncertaity="deterministic")
```

## Development

Run tests:

```bash
uv run python -m pytest
```

Regenerate docs pages and build site:

```bash
uv run python docs/scripts/generate_trait_docs.py
uv run mkdocs build -f docs/mkdocs.yml --strict
```

## Inspirations, prior work

This implementation builds directly on patterns established in:

- [`mlcast-dataset-validator`](https://github.com/mlcast-community/mlcast-dataset-validator): inline markdown specs + check functions + docs rendering/deployment workflow.
- [`mxalign`](https://github.com/rmi-mlwp/mxalign): trait/property model for `space`, `time`, and `uncertainty`.
