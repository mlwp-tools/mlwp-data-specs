# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Uncertainty trait specification bumped to 0.2.0
  ([#34](https://github.com/mlwp-tools/mlwp-data-specs/issues/34)):
  - `deterministic`: no `member` or `quantile` dimension; a scalar `member`
    coordinate is allowed.
  - `ensemble`: `member` is 1-D with unique integer values and `units = "1"`.
  - `member` and `quantile` must be the first dimension of every data variable.
  - `quantile` no longer requires `standard_name = "quantile"` (not a CF name).
  - Recommends `cell_methods` (e.g. `realization: mean`) on ensemble-reduced
    data; not checked.

### Added

- `check_for_forbidden_dims`, `check_leading_dim` and
  `check_member_coordinate_values` checks.

## [0.1.0](https://github.com/mlwp-tools/mlwp-data-specs/releases/tag/v0.1.0)

First release of `mlwp-data-specs`, a trait-based dataset specification and
validation package for MLWP weather/climate datasets.

### Added

- Trait-based validation across `time`, `space`, and `uncertainty` axes.
- Supported time traits: `forecast` and `observation`.
- Supported space traits: `grid` and `point`.
- Supported uncertainty traits: `deterministic`, `ensemble`, and `quantile`.
- Public Python API via `mlwp_data_specs.validate_dataset(...)`.
- CLI entry point via `mlwp.validate_dataset_traits`.
- Dataset trait resolution from global attributes such as `mlwp_time_trait`,
  `mlwp_space_trait`, and `mlwp_uncertainty_trait`.
- Validation reporting with pass/warn/fail checks.
- Local and remote Zarr validation through `xarray.open_zarr`, including optional
  S3 storage options.
- Inline executable markdown specifications colocated with validation checks.
- Generated documentation for trait specifications.
- Dynamic package versioning from SCM and public `mlwp_data_specs.__version__`.
