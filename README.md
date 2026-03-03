# mlwp-data-specs

[![Spec Docs](https://img.shields.io/badge/spec%20docs-HTML-blue)](https://leifdenby.github.io/mlwp-data-specs/)

Trait-based dataset validator for weather/climate datasets in Zarr format.

## Why this was made

To facilitate comparing forecasts from MLWP (Machine Learning Weather Prediction) models this validator implements a specification so that a single well-defined format can be targeted. The motivation for this to allow different groups to share their forecasts in a common format so that general-purpose tooling can be built to examine these forecasts.

Multiple projects in ML weather pipelines need consistent, machine-checkable guarantees around coordinate structure and metadata. This repository was created to:

1. make trait-level dataset requirements explicit (`time`, `space`, `uncertainty`)
2. keep human-readable spec text and executable validation logic side-by-side
3. provide both CLI and Python APIs for local and remote Zarr validation
4. publish linkable HTML spec docs directly from the validator code

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
│   └── traits/
│       ├── spatial_coordinate.py # Inline spatial trait specs + validation wiring
│       ├── time_coordinate.py    # Inline time trait specs + validation wiring
│       └── uncertainty.py        # Inline uncertainty trait specs + validation wiring
├── checks/
│   ├── traits/
│   │   └── structure.py          # Dimension/required-coordinate checks
│   └── metadata/
│       └── coords.py             # standard_name/units/etc checks
└── traits/
    ├── cli.py                    # CLI entry point (mlwp.validate_dataset_traits)
    ├── properties.py             # Space/Time/Uncertainty enums
    ├── specs.py                  # Trait structural spec tables (mxalign-style)
    └── reporting.py              # ValidationReport and check registry helpers
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
uv run mkdocs build --strict
```

## Inspirations, prior work

This implementation builds directly on patterns established in:

- [`mlcast-dataset-validator`](https://github.com/mlcast-community/mlcast-dataset-validator): inline markdown specs + check functions + docs rendering/deployment workflow.
- [`mxalign`](https://github.com/rmi-mlwp/mxalign): trait/property model for `space`, `time`, and `uncertainty`.
