import collections
import tempfile
from pathlib import Path
from shutil import rmtree
from typing import Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from pywps import configuration
from scipy.stats import norm, uniform
from xarray import DataArray
from xclim.core.calendar import percentile_doy
from xclim.testing.helpers import (
    test_timeseries as timeseries,  # pr_hr_series, pr_series, q_series, tas_series
)

import finch.processes
import finch.wsgi
from _common import CFG_FILE, client_for

TEMP_DIR = Path(__file__).parent / "tmp"


@pytest.fixture(scope="session", autouse=True)
def setup_temp_data(request):
    TEMP_DIR.mkdir(exist_ok=True)

    def _cleanup_temp():
        rmtree(TEMP_DIR, ignore_errors=True)

    request.addfinalizer(_cleanup_temp)


def _create_test_dataset(
    variable: str,
    cell_methods: str,
    standard_name: str,
    units: str,
    seed: Optional[Union[int, float, np.ndarray]] = None,
    missing: bool = False,
):
    """Create a synthetic dataset for variable.

    Parameters
    ----------
    variable : str
    cell_methods : str
    standard_name : str
    units : str
    seed : int, float, array_like, optional
    missing : bool
        If True, add a NaN on Jan 15.
    """

    rs = np.random.RandomState(seed)
    _vars = {variable: ["time", "lon", "lat"]}
    _dims = {"time": 365, "lon": 5, "lat": 6}
    _attrs = {
        variable: dict(
            units=units, cell_methods=cell_methods, standard_name=standard_name
        )
    }

    attrs = {
        "Conventions": "CF-1.4",
        "frequency": "day",
        "modeling_realm": "atmos",
        "project_id": "CMIP5",
        "driving_experiment": "historical,rcp85",
        "driving_experiment_id": "historical,rcp85",
        "driving_model_id": "dummy-model",
        "driving_realization": "1",
        "driving_initialization_method": "1",
        "driving_physics_version": "1",
    }

    obj = xr.Dataset(attrs=attrs)
    obj["time"] = ("time", pd.date_range("2000-01-01", periods=_dims["time"]))
    obj["lon"] = ("lon", np.arange(_dims["lon"]), {"standard_name": "longitude"})
    obj["lat"] = ("lat", np.arange(_dims["lat"]), {"standard_name": "latitude"})

    for v, dims in sorted(_vars.items()):
        data = rs.normal(size=tuple(_dims[d] for d in dims))
        if missing:
            data[14, :, :] = np.nan
        obj[v] = (dims, data, {"foo": "variable"})
        obj[v].attrs.update(_attrs[v])

    return obj


def _create_and_write_dataset(variable, **kwds) -> Path:
    """Write a DataSet to disk and return its path"""
    ds = _create_test_dataset(variable, **kwds)
    return _write_dataset(variable, ds)


def _write_dataset(variable, ds) -> Path:
    _, filename = tempfile.mkstemp(f"finch_test_data_{variable}.nc", dir=TEMP_DIR)
    ds.to_netcdf(filename)
    return Path(filename)


variable_descriptions = {
    # variable_name: (cell_methods, standard_name, units)
    "tas": {
        "cell_methods": "time: mean within days",
        "standard_name": "air_temperature",
        "units": "K",
    },
    "tasmax": {
        "cell_methods": "time: maximum within days",
        "standard_name": "air_temperature",
        "units": "K",
    },
    "tasmin": {
        "cell_methods": "time: minimum within days",
        "standard_name": "air_temperature",
        "units": "K",
    },
    "pr": {
        "cell_methods": "time: mean",
        "standard_name": "precipitation_flux",
        "units": "mm/d",
    },
    "prsn": {
        "cell_methods": "time: mean",
        "standard_name": "snowfall_flux",
        "units": "mm/d",
    },
    "discharge": {
        "cell_methods": "time: mean",
        "standard_name": "water_volume_transport_in_river_channel",
        "units": "m^3 s-1",
    },
}


@pytest.fixture(scope="session")
def netcdf_datasets(request) -> Dict[str, Path]:
    """Returns a Dict mapping a variable name to a corresponding netcdf path"""
    datasets = dict()
    for variable_name, description in variable_descriptions.items():
        filename = _create_and_write_dataset(variable_name, **description, seed=1)
        datasets[variable_name] = filename

        # With missing values
        filename = _create_and_write_dataset(
            variable_name, **description, seed=1, missing=True
        )
        datasets[variable_name + "_missing"] = filename

    tasmin = xr.open_dataset(datasets["tasmin"]).tasmin
    tas = xr.open_dataset(datasets["tas"]).tas

    tn10 = percentile_doy(tasmin, per=0.1).to_dataset(name="tn10")
    datasets["tn10"] = _write_dataset("tn10", tn10)
    t10 = percentile_doy(tas, per=0.1).to_dataset(name="t10")
    datasets["t10"] = _write_dataset("t10", t10)
    t90 = percentile_doy(tas, per=0.9).to_dataset(name="t90")
    datasets["t90"] = _write_dataset("t90", t90)

    # Create file with two variables
    keys = ["pr", "discharge"]
    ds = xr.merge(
        [_create_test_dataset(k, **variable_descriptions[k], seed=1) for k in keys]
    )
    datasets["pr_discharge"] = _write_dataset("pr_discharge", ds)

    return datasets


@pytest.fixture(scope="session")
def netcdf_sdba_ds(request) -> Tuple[Dict[str, Path], DataArray]:
    """Return datasets useful to test sdba."""
    out = {}
    u = np.random.rand(10000)

    # Define distributions
    xd = uniform(loc=10, scale=1)
    yd = norm(loc=12, scale=1)

    # Generate random numbers with u, so we get exact results for comparison
    x = xd.ppf(u)
    y = yd.ppf(u)

    # Test train
    out["qdm_tas_hist"] = _write_dataset("qdm_tas_hist", series(x, "tas"))
    out["qdm_tas_ref"] = _write_dataset("qdm_tas_ref", series(y, "tas"))
    out["qdm_pr_hist"] = _write_dataset("qdm_pr_hist", series(x, "pr"))
    out["qdm_pr_ref"] = _write_dataset("qdm_pr_ref", series(y, "pr"))

    return out, series(u, "u")


@pytest.fixture(scope="module")
def client():
    service = finch.wsgi.create_app(cfgfiles=CFG_FILE)

    # overwrite output path from defaults.cfg
    outputpath = tempfile.gettempdir()
    configuration.CONFIG.set("server", "outputurl", f"file://{outputpath}")
    configuration.CONFIG.set("server", "outputpath", outputpath)

    return client_for(service)


def series(values: np.ndarray, name: str, start: str = "2000-01-01"):
    coords = collections.OrderedDict()
    for dim, n in zip(("time", "lon", "lat"), values.shape):
        if dim == "time":
            coords[dim] = pd.date_range(start, periods=n, freq=pd.DateOffset(days=1))
        else:
            coords[dim] = xr.IndexVariable(dim, np.arange(n))

    if name == "tas":
        attrs = {
            "standard_name": "air_temperature",
            "cell_methods": "time: mean within days",
            "units": "K",
            "kind": "+",
        }
    elif name == "pr":
        attrs = {
            "standard_name": "precipitation_flux",
            "cell_methods": "time: sum over day",
            "units": "kg m-2 s-1",
            "kind": "*",
        }
    else:
        attrs = {}

    return xr.DataArray(
        values,
        coords=coords,
        dims=list(coords.keys()),
        name=name,
        attrs=attrs,
    )


@pytest.fixture
def hourly_dataset():  # noqa: F811
    """Ten days of precip with first hour missing."""
    a = np.arange(10 * 24.0)
    a[0] = np.nan
    return _write_dataset("pr_hr", timeseries(values=a, variable="pr", freq="H"))
