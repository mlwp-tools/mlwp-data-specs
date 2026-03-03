import xarray as xr

from mlwp_data_specs.traits.properties import Uncertainty
from mlwp_data_specs.traits.uncertainty import validate_dataset


def _quantile_ds(values, with_attrs=True):
    ds = xr.Dataset(coords={"quantile": ("quantile", values)})
    if with_attrs:
        ds.coords["quantile"].attrs.update({"standard_name": "quantile", "units": "1"})
    return ds


def test_uncertainty_quantile_passes():
    report, _ = validate_dataset(_quantile_ds([0.1, 0.5, 0.9]), trait=Uncertainty.QUANTILE)
    assert not report.has_fails()


def test_uncertainty_quantile_fails_out_of_bounds():
    report, _ = validate_dataset(_quantile_ds([-0.1, 0.5, 1.1]), trait=Uncertainty.QUANTILE)
    assert report.has_fails()
