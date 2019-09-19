import os
from pathlib import Path

import pytest
import tempfile

from pywps import Service
from pywps.tests import client_for

import finch
import finch.processes
from .common import CFG_FILE


def _create_test_dataset(variable, cell_methods, stardard_name, seed=None):
    """Create a synthetic dataset for variable"""
    import numpy as np
    import xarray as xr
    import pandas as pd

    rs = np.random.RandomState(seed)
    _vars = {variable: ["time", "lon", "lat"]}
    _dims = {"time": 365, "lon": 5, "lat": 6}
    _attrs = {
        variable: dict(
            units="K", cell_methods=cell_methods, standard_name=stardard_name
        )
    }

    obj = xr.Dataset()
    obj["time"] = ("time", pd.date_range("2000-01-01", periods=_dims["time"]))
    obj["lon"] = ("lon", np.arange(_dims["lon"]))
    obj["lat"] = ("lat", np.arange(_dims["lat"]))

    for v, dims in sorted(_vars.items()):
        data = rs.normal(size=tuple(_dims[d] for d in dims))
        obj[v] = (dims, data, {"foo": "variable"})
        obj[v].attrs.update(_attrs[v])

    return obj


def _write_dataset(variable, cell_methods, standard_name, seed=None):
    """Write a DataSet to disk and return its path"""
    ds = _create_test_dataset(variable, cell_methods, standard_name, seed)
    dir_name = Path(__file__).parent / "tmp"
    dir_name.mkdir(exist_ok=True)
    _, filename = tempfile.mkstemp(f"finch_test_data{variable}.nc", dir=dir_name)
    ds.to_netcdf(filename)
    return filename


variable_descriptions = {
    # variable_name: (variable_name, cell_methods, stardard_name)
    "tas": ("tas", "time: mean within days", "air_temperature"),
    "tasmax": ("tasmax", "time: maximum within days", "air_temperature"),
    "tasmin": ("tasmin", "time: minimum within days", "air_temperature"),
    "pr": ("pr", "time: mean", "precipitation_flux"),
}


@pytest.fixture(scope='module')
def tas_dataset(request):
    filename = _write_dataset(*variable_descriptions["tas"])
    request.addfinalizer(lambda: os.remove(filename))
    return filename


@pytest.fixture(scope='module')
def tasmax_dataset(request):
    filename = _write_dataset(*variable_descriptions["tasmax"])
    request.addfinalizer(lambda: os.remove(filename))
    return filename


@pytest.fixture(scope='module')
def tasmin_dataset(request):
    filename = _write_dataset(*variable_descriptions["tasmin"])
    request.addfinalizer(lambda: os.remove(filename))
    return filename


@pytest.fixture(scope="module")
def client():
    return client_for(Service(processes=finch.processes.processes, cfgfiles=CFG_FILE))
