# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- Restructured `mlwp_data_specs.checks` to mirror xr.Dataset components (as in
  `mlcast-dataset-validator`): `checks.traits._common` and `checks.metadata.coords`
  are replaced by `checks.coords.{dimensions,names,spatial,temporal,uncertainty}`.
- Renamed `AxisName` to `TraitAxis` and the `axis=` keyword of
  `check_dim_variants`/`check_required_coords` to `trait_axis=`, to avoid confusion
  with array dimension axes.
- Bumped the `spatial_coordinate` spec version to `0.1.1-draft` (wording: "spatial
  axis" → "spatial trait axis").
- Trait specs now include a "Global Attributes" section: datasets MAY declare
  `mlwp_{time,space,uncertainty}_trait`; if present the value MUST be a valid
  profile (FAIL otherwise) and SHOULD match the validated profile (WARNING
  otherwise). Previously invalid/mismatching values were only logged. An invalid
  value is reported even when that trait is not being validated (e.g.
  `validate_dataset(ds, space="grid")` with `mlwp_time_trait="nowcast"`). All
  trait spec versions are now `0.1.1-draft`.
  [\#38](https://github.com/mlwp-tools/mlwp-data-specs/pull/38), @leifdenby
- Trait profile classes `Space`, `Time` and `Uncertainty` are now `StrEnumLike`
  classes (defined in `mlwp_data_specs.trait_profiles`, still importable from the
  trait spec modules) instead of `enum.Enum`s. Their members are plain `str`, so
  they can be set as dataset attributes (e.g. `mlwp_space_trait`) and saved to
  netCDF/zarr without casting. Usage like `Space.GRID` is unchanged. **Upgrade
  note**, only for enum-specific usage: `.value`/`.name` and construction such as
  `Space("grid")` no longer exist (use `Space.GRID`, or `value in Space` to
  check a string), `isinstance(x, Space)` no longer holds, and `str(Space.GRID)`
  is now `"grid"` rather than `"Space.GRID"`.
  [\#42](https://github.com/mlwp-tools/mlwp-data-specs/pull/42), @leifdenby

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
