import zipfile
from pathlib import Path

import numpy as np
import pytest
import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for

from _common import CFG_FILE, get_output
from _utils import execute_process, wps_literal_input
from finch.processes import SubsetBboxProcess


def test_wps_subsetbbox(netcdf_datasets):
    client = client_for(Service(processes=[SubsetBboxProcess()], cfgfiles=CFG_FILE))

    datainputs = (
        f"resource=files@xlink:href=file://{netcdf_datasets['tas']};"
        "lat0=2;"
        "lon0=3;"
        "lat1=4;"
        "lon1=5;"
        "start_date=2000;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_bbox&datainputs={datainputs}"
    )

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out["output"][7:])
    np.testing.assert_array_equal(ds.lat, [2, 3, 4])
    np.testing.assert_array_equal(ds.lon, [3, 4])


@pytest.mark.parametrize("outfmt", ["netcdf", "csv"])
def test_wps_subsetbbox_dataset(client, outfmt):
    # --- given ---
    identifier = "subset_bbox_dataset"
    inputs = [
        wps_literal_input("lat0", "45"),
        wps_literal_input("lon0", "-74"),
        wps_literal_input("lat1", "46"),
        wps_literal_input("lon1", "-73"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("output_format", outfmt),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    assert (
        Path(outputs[0]).stem
        == "test_subset_subset_bbox_dataset_45_000_74_000_46_000_73_000_rcp45"
    )

    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == (4 if outfmt == "netcdf" else 5)

    if outfmt == "netcdf":
        data_filenames = [n for n in zf.namelist() if "metadata" not in n]

        with zf.open(data_filenames[0]) as f:
            ds = xr.open_dataset(f)

            dims = dict(ds.dims)
            assert dims == {
                "lon": 6,
                "lat": 6,
                "time": 100,
            }
