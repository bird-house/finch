from pathlib import Path
from shutil import rmtree
import tempfile
from typing import Dict

import pytest
from pywps import configuration
import xarray as xr
from xclim.utils import percentile_doy

import finch.processes
import finch.wsgi

from .common import CFG_FILE, client_for


TEMP_DIR = Path(__file__).parent / "tmp"


@pytest.fixture(scope="session", autouse=True)
def setup_temp_data(request):
    TEMP_DIR.mkdir(exist_ok=True)

    def _cleanup_temp():
        rmtree(TEMP_DIR, ignore_errors=True)

    request.addfinalizer(_cleanup_temp)


def _create_test_dataset(variable, cell_methods, stardard_name, units, seed=None):
    """Create a synthetic dataset for variable"""
    import numpy as np
    import xarray as xr
    import pandas as pd

    rs = np.random.RandomState(seed)
    _vars = {variable: ["time", "lon", "lat"]}
    _dims = {"time": 365, "lon": 5, "lat": 6}
    _attrs = {
        variable: dict(
            units=units, cell_methods=cell_methods, standard_name=stardard_name
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


def _create_and_write_dataset(
    variable, cell_methods, standard_name, units, seed=None
) -> Path:
    """Write a DataSet to disk and return its path"""
    ds = _create_test_dataset(variable, cell_methods, standard_name, units, seed)
    return _write_dataset(variable, ds)


def _write_dataset(variable, ds) -> Path:
    _, filename = tempfile.mkstemp(f"finch_test_data{variable}.nc", dir=TEMP_DIR)
    ds.to_netcdf(filename)
    return Path(filename)


variable_descriptions = {
    # variable_name: (cell_methods, stardard_name, units)
    "tas": ("time: mean within days", "air_temperature", "K"),
    "tasmax": ("time: maximum within days", "air_temperature", "K"),
    "tasmin": ("time: minimum within days", "air_temperature", "K"),
    "pr": ("time: mean", "precipitation_flux", "mm/d"),
    "prsn": ("time: mean", "snowfall_flux", "mm/d"),
}


@pytest.fixture(scope="session")
def netcdf_datasets(request) -> Dict[str, Path]:
    """Returns a Dict mapping a variable name to a corresponding netcdf path"""
    datasets = {}
    for variable_name, description in variable_descriptions.items():
        filename = _create_and_write_dataset(variable_name, *description, seed=1)
        datasets[variable_name] = filename

    tasmin = xr.open_dataset(datasets["tasmin"]).tasmin
    tas = xr.open_dataset(datasets["tas"]).tas

    tn10 = percentile_doy(tasmin, per=0.1).to_dataset(name="tn10")
    datasets["tn10"] = _write_dataset("tn10", tn10)
    t10 = percentile_doy(tas, per=0.1).to_dataset(name="t10")
    datasets["t10"] = _write_dataset("t10", t10)
    t90 = percentile_doy(tas, per=0.9).to_dataset(name="t90")
    datasets["t90"] = _write_dataset("t90", t90)

    return datasets


@pytest.fixture(scope="module")
def client():
    service = finch.wsgi.create_app(cfgfiles=CFG_FILE)

    # overwrite output path from defaults.cfg
    outputpath = tempfile.gettempdir()
    configuration.CONFIG.set("server", "outputurl", f"file://{outputpath}")
    configuration.CONFIG.set("server", "outputpath", outputpath)

    return client_for(service)
