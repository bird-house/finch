import zipfile
from unittest import mock
from pathlib import Path

import pytest
import xarray as xr
from netCDF4 import Dataset

from tests.utils import wps_literal_input, execute_process
from finch.processes.wps_xsubsetpoint_bccaqv2 import SubsetGridPointBCCAQV2Process
from finch.processes.wps_xsubsetbbox_bccaqv2 import SubsetBboxBCCAQV2Process


@pytest.fixture
def mock_local_datasets(monkeypatch):
    from pywps.configuration import CONFIG
    from finch.processes import utils

    CONFIG.set("finch", "bccaqv2_url", '/mock_local/path')

    test_data = Path(__file__).parent / "data" / "bccaqv2_subset_sample" / "tasmin_subset.nc"

    monkeypatch.setattr(utils, "get_bccaqv2_local_files_datasets", lambda *args: [f"{test_data}"])


def test_bccaqv2_subset_point(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat", "46.0"),
        wps_literal_input("lon", "-72.8"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 1
    ds = Dataset('inmemory.nc', memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {'lat': 1, 'lon': 1, 'time': 100}


def test_bccaqv2_subset_point_csv(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat", "46.0"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if not 'metadata' in n]
    csv = zf.read(data_filename[0])
    n_lines = csv.count(b'\n') - 1
    assert n_lines == 100
    


def test_bccaqv2_subset_point_multiple(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat", "46.0, 46.1, 46.1"),
        wps_literal_input("lon", "-72.8, -72.7, -72.9"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 1
    ds = Dataset('inmemory.nc', memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {'lat': 2, 'lon': 3, 'time': 100}


def test_bccaqv2_subset_point_multiple_csv(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat", "46.0, 46.1, 46.1"),
        wps_literal_input("lon", "-72.8, -72.7, -72.9"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if not 'metadata' in n]
    csv = zf.read(data_filename[0])
    n_lines = csv.count(b'\n') - 1
    assert n_lines == 300


def test_bccaqv2_subset_point_multiple_same_cell(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat", "46.0, 46.0"),  # The coordinates pairs are the same
        wps_literal_input("lon", "-72.8, -72.8"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 1
    ds = Dataset('inmemory.nc', memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {'lat': 1, 'lon': 1, 'time': 100}  


def test_bccaqv2_subset_point_lat0_lon0_deprecation(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lon0", "-72.8"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    zf = zipfile.ZipFile(outputs[0])
    ds = Dataset('inmemory.nc', memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {'lat': 1, 'lon': 1, 'time': 100}


def test_bccaqv2_subset_bbox_process(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_bbox_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-73.0"),
        wps_literal_input("lon1", "-72.8"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 1
    ds = Dataset('inmemory.nc', memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {'lat': 2, 'lon': 2, 'time': 100}


def test_bccaqv2_subset_bbox_process_csv(mock_local_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_bbox_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-73.0"),
        wps_literal_input("lon1", "-72.8"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if not 'metadata' in n]
    csv = zf.read(data_filename[0])
    n_lines = csv.count(b'\n') - 1
    assert n_lines == 400


@pytest.mark.skip('Skipping: subset using real data is too long.')
def test_bccaqv2_subset_online(client):
    identifier = "subset_ensemble_BCCAQv2"
    up_right = 45.507485, -73.541295
    bottom_left = 45.385644, -73.691963

    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lon0", str(bottom_left[1])),
        wps_literal_input("lon1", str(up_right[1])),
        wps_literal_input("lat0", str(bottom_left[0])),
        wps_literal_input("lat1", str(up_right[0])),
        wps_literal_input("y0", "2010"),
        wps_literal_input("y1", "2011"),
    ]

    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    print(outputs)
