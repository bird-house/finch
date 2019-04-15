import pytest


@pytest.fixture
def create_test_dataset():
    def _create_test_dataset(var='tas', seed=None):
        """Create a synthetic dataset for variable"""
        import numpy as np
        import xarray as xr
        import pandas as pd

        rs = np.random.RandomState(seed)
        _vars = {var: ['time', 'lon', 'lat']}
        _dims = {'time': 365, 'lon': 5, 'lat': 6}
        _attrs = {var: dict(units='K', cell_methods='time: mean within days', standard_name='air_temperature')}

        obj = xr.Dataset()
        obj['time'] = ('time', pd.date_range('2000-01-01', periods=_dims['time']))
        obj['lon'] = ('lon', np.arange(_dims['lon']))
        obj['lat'] = ('lat', np.arange(_dims['lat']))

        for v, dims in sorted(_vars.items()):
            data = rs.normal(size=tuple(_dims[d] for d in dims))
            obj[v] = (dims, data, {'foo': 'variable'})
            obj[v].attrs.update(_attrs[v])

        return obj

    return _create_test_dataset


@pytest.fixture
def tas_data_set(create_test_dataset, tmp_path_factory):
    ds = create_test_dataset('tas')
    fn = tmp_path_factory.mktemp('data') / 'tas.nc'
    ds.to_netcdf(str(fn))
    return str(fn)


@pytest.fixture
def tasmin_data_set(create_test_dataset, tmp_path_factory):
    ds = create_test_dataset('tasmin')
    fn = tmp_path_factory.mktemp('data') / 'tasmin.nc'
    ds.to_netcdf(str(fn))
    return str(fn)


@pytest.fixture
def tasmax_data_set(create_test_dataset, tmp_path_factory):
    ds = create_test_dataset('tasmax')
    fn = tmp_path_factory.mktemp('data') / 'tasmax.nc'
    ds.to_netcdf(str(fn))
    return str(fn)
