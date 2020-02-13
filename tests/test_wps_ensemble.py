from pathlib import Path
import zipfile

from netCDF4 import Dataset
import pytest

from tests.utils import execute_process, wps_literal_input, mock_local_datasets


@pytest.fixture
def mock_datasets(monkeypatch):
    filenames = ["tasmin_subset.nc", "tasmax_subset.nc"]
    mock_local_datasets(monkeypatch, filenames=filenames)


def test_ensemble_heatwave_frequency(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
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
