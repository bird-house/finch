import zipfile
from pathlib import Path

import pytest
import xarray as xr
from numpy.testing import assert_array_equal
from pywps import Service
from pywps.tests import assert_response_success, client_for

from _common import CFG_FILE, get_metalinks, get_output
from _utils import execute_process, wps_literal_input
from finch.processes import SubsetGridPointProcess


def test_wps_xsubsetpoint(netcdf_datasets):
    client = client_for(
        Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE)
    )

    datainputs = (
        f"resource=files@xlink:href=file://{netcdf_datasets['tas']};"
        "lat=2.0;"
        "lon=3.0;"
        "start=2000;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={datainputs}"
    )

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out["output"][7:])
    assert ds.lat == 2
    assert ds.lon == 3


def test_wps_multiple_xsubsetpoint(netcdf_datasets):
    client = client_for(
        Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE)
    )

    datainputs = (
        f"resource=files@xlink:href=file://{netcdf_datasets['tas']};"
        "lat=1.0,3.0,4.0;"
        "lon=2.0,3.0,4.0;"
        "start=2000;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={datainputs}"
    )

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out["output"][7:])
    assert_array_equal(ds.lon, [2, 3, 4])
    assert_array_equal(ds.lat, [1, 3, 4])


@pytest.mark.online
def test_thredds():
    import lxml.etree

    client = client_for(
        Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE)
    )
    fn1 = (
        "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/"
        "birdhouse/disk2/cmip5/MRI/rcp85/fx/atmos/r0i0p0/sftlf/sftlf_fx_MRI-CGCM3_rcp85_r0i0p0.nc"
    )
    fn2 = (
        "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/"
        "birdhouse/disk2/cmip5/MRI/rcp85/fx/atmos/r0i0p0/orog/orog_fx_MRI-CGCM3_rcp85_r0i0p0.nc"
    )

    datainputs = (
        f"resource=files@xlink:href={fn1};"
        f"resource=files@xlink:href={fn2};"
        "lat=45.0;"
        "lon=150.0;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={datainputs}"
    )

    assert_response_success(resp)
    out = get_output(resp.xml)
    links = get_metalinks(lxml.etree.fromstring(out["ref"].encode()))
    assert len(links) == 2


@pytest.mark.online
def test_bad_link_on_thredds():
    client = client_for(
        Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE)
    )
    fn = "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/disk2/cmip5/bad_link.nc"
    datainputs = f"resource=files@xlink:href={fn};" "lat=45.0;" "lon=150.0;"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={datainputs}"
    )

    assert "NetCDF: file not found" in resp.response[0].decode()


def test_bad_link_on_fs():
    client = client_for(
        Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE)
    )
    fn = "file://tmp/bad_link.nc"
    datainputs = f"resource=files@xlink:href={fn};" "lat=45.0;" "lon=150.0;"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={datainputs}"
    )

    assert "No such file or directory" in resp.response[0].decode()


@pytest.mark.parametrize("outfmt", ["netcdf", "csv"])
def test_wps_subsetpoint_dataset(client, outfmt):
    # --- given ---
    identifier = "subset_grid_point_dataset"
    inputs = [
        wps_literal_input("lat", "45"),
        wps_literal_input("lon", "-74"),
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
        == "test_subset_subset_grid_point_dataset_45_000_74_000_rcp45"
    )

    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == (4 if outfmt == "netcdf" else 5)

    if outfmt == "netcdf":
        data_filenames = [n for n in zf.namelist() if "metadata" not in n]

        with zf.open(data_filenames[0]) as f:
            ds = xr.open_dataset(f)

            dims = dict(ds.dims)
            assert dims == {
                "region": 1,
                "time": 100,
            }
