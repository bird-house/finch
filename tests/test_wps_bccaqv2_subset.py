from pathlib import Path
import zipfile

from netCDF4 import Dataset
import pytest

from tests.utils import execute_process, mock_local_datasets, wps_literal_input


@pytest.fixture
def mock_datasets(monkeypatch):
    filenames = ["tasmin_subset.nc"]
    mock_local_datasets(monkeypatch, filenames=filenames)


def test_bccaqv2_subset_point(mock_datasets, client):
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
    ds = Dataset("inmemory.nc", memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {"region": 1, "time": 100}


def test_bccaqv2_subset_point_csv(mock_datasets, client):
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
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0])
    n_lines = csv.count(b"\n") - 1
    assert n_lines == 100


def test_bccaqv2_subset_point_multiple(mock_datasets, client):
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
    ds = Dataset("inmemory.nc", memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {"region": 3, "time": 100}


def test_bccaqv2_subset_point_multiple_csv(mock_datasets, client):
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
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0])
    n_lines = csv.count(b"\n") - 1
    assert n_lines == 300


def test_bccaqv2_subset_point_multiple_same_cell(mock_datasets, client):
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
    ds = Dataset("inmemory.nc", memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}

    # Todo: the cells are concatenated: is this the desired behaviour?
    assert dims == {"region": 2, "time": 100}


def test_bccaqv2_subset_point_lat0_lon0_deprecation(mock_datasets, client):
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
    ds = Dataset("inmemory.nc", memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {"region": 1, "time": 100}


def test_bccaqv2_subset_bbox_process(mock_datasets, client):
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
    ds = Dataset("inmemory.nc", memory=zf.read(zf.namelist()[0]))
    dims = {d.name: d.size for d in ds.dimensions.values()}
    assert dims == {"lat": 2, "lon": 2, "time": 100}


def test_bccaqv2_subset_bbox_process_csv(mock_datasets, client):
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
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0])
    n_lines = csv.count(b"\n") - 1
    assert n_lines == 400


@pytest.mark.skip("Skipping: subset using real data is too long.")
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
