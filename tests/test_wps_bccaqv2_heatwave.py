from pathlib import Path
import zipfile

from netCDF4 import Dataset
import pytest

from tests.utils import execute_process, wps_literal_input


@pytest.fixture
def mock_local_datasets(monkeypatch):
    """Mock the get_bccaqv2_local_files_datasets function

    >>> tasmax  # "tasmax_subset.nc"
    <xarray.Dataset>
    Dimensions:  (lat: 12, lon: 12, time: 100)
    Coordinates:
    * lon      (lon) float64 -73.46 -73.38 -73.29 -73.21 ... -72.71 -72.63 -72.54
    * lat      (lat) float64 45.54 45.62 45.71 45.79 ... 46.21 46.29 46.37 46.46
    * time     (time) object 1950-01-01 12:00:00 ... 1950-04-10 12:00:00
    Data variables:
        tasmax   (time, lat, lon) float32 ...
    >>> tasmin  # "tasmin_subset.nc"
    <xarray.Dataset>
    Dimensions:  (lat: 12, lon: 12, time: 100)
    Coordinates:
    * lon      (lon) float64 -73.46 -73.38 -73.29 -73.21 ... -72.71 -72.63 -72.54
    * lat      (lat) float64 45.54 45.62 45.71 45.79 ... 46.21 46.29 46.37 46.46
    * time     (time) object 1950-01-01 12:00:00 ... 1950-04-10 12:00:00
    Data variables:
        tasmin   (time, lat, lon) float32 ...
    """
    from pywps.configuration import CONFIG
    from finch.processes import utils_bccaqv2

    CONFIG.set("finch", "bccaqv2_url", "/mock_local/path")

    subset_sample = Path(__file__).parent / "data" / "bccaqv2_subset_sample"

    test_data = [
        subset_sample / "tasmin_subset.nc",
        subset_sample / "tasmax_subset.nc",
    ]

    monkeypatch.setattr(
        utils_bccaqv2,
        "get_bccaqv2_local_files_datasets",
        lambda *args: [str(f) for f in test_data],
    )


def test_bccaqv2_heatwave_frequency(mock_local_datasets, client):
    # --- given ---
    identifier = "BCCAQv2_heat_wave_frequency_gridpoint"
    inputs = [
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 1
    ds = Dataset("inmemory.nc", memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {
        "region": 1,
        "time": 4,  # there are roughly 4 months in the test datasets
    }
