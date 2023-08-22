from pathlib import Path

import numpy as np
import xarray as xr

from _utils import execute_process, wps_input_file, wps_literal_input


def geomet_geojson():
    return (Path(__file__).parent / "data" / "geomet.geojson").as_posix()


def test_wps_geoseries_to_netcdf(client):
    identifier = "geoseries_to_netcdf"
    inputs = [
        wps_input_file("resource", geomet_geojson()),
        wps_literal_input("index_dim", "LOCAL_DATE"),
    ]
    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        assert set(ds.dims) == {"features", "LOCAL_DATE"}
        assert ds.features.size == 23
        assert np.issubdtype(ds.LOCAL_DATE.dtype, np.datetime64)
        print(ds.attrs)


def test_wps_geoseries_to_netcdf_feat_squeeze(client):
    identifier = "geoseries_to_netcdf"
    inputs = [
        wps_input_file("resource", geomet_geojson()),
        wps_literal_input("index_dim", "LOCAL_DATE"),
        wps_literal_input("feat_dim", "STATION_NAME"),
        wps_literal_input("squeeze", "True"),
    ]
    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        assert set(ds.dims) == {"STATION_NAME", "LOCAL_DATE"}
        assert ds.STATION_NAME.size == 23
        assert set(ds.CLIMATE_IDENTIFIER.dims) == {"STATION_NAME"}
