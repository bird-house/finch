import zipfile
from unittest import mock
from pathlib import Path

import pytest
import xarray as xr

from tests.utils import wps_literal_input, execute_process
from finch.processes.wps_xsubsetpoint_bccaqv2 import SubsetGridPointBCCAQV2Process
from finch.processes.wps_xsubsetbbox_bccaqv2 import SubsetBboxBCCAQV2Process


@mock.patch("finch.processes.utils.get_bccaqv2_local_files_datasets")
def test_bccaqv2_subset_point(mock_datasets, client):
    # --- given ---
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lon0", "-72.8"),
    ]

    from pywps.configuration import CONFIG

    CONFIG.set("finch", "bccaqv2_url", '/mock_local/path')
    test_data = Path(__file__).parent / "data" / "bccaqv2_subset_sample" / "tasmin_subset.nc"
    mock_datasets.return_value = [f"{test_data}"]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    output_file = outputs[0]
    assert len(outputs) == 1

    zf = zipfile.ZipFile(output_file)
    infolist = zf.infolist()
    assert len(infolist) == 1
    tmp = Path(__file__).parent / "tmp"
    zf.extract(infolist[0], tmp)
    ds = xr.open_dataset(str(tmp / infolist[0].filename))
    assert dict(ds.dims) == {'time': 100}


@mock.patch("finch.processes.utils.get_bccaqv2_local_files_datasets")
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

    from pywps.configuration import CONFIG

    CONFIG.set("finch", "bccaqv2_url", '/mock_local/path')
    test_data = Path(__file__).parent / "data" / "bccaqv2_subset_sample" / "tasmin_subset.nc"
    mock_datasets.return_value = [f"{test_data}"]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    output_file = outputs[0]

    assert len(outputs) == 1

    zf = zipfile.ZipFile(output_file)
    infolist = zf.infolist()
    assert len(infolist) == 1
    tmp = Path(__file__).parent / "tmp"
    zf.extract(infolist[0], tmp)
    ds = xr.open_dataset(str(tmp / infolist[0].filename))
    assert dict(ds.dims) == {'lat': 2, 'lon': 2, 'time': 100}


@pytest.mark.online
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
        wps_literal_input("y1", "2010"),
    ]

    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    print(outputs)
