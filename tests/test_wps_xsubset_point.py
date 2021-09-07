import pytest
import xarray as xr
from numpy.testing import assert_array_equal
from pywps import Service
from pywps.tests import assert_response_success, client_for

from finch.processes import SubsetGridPointProcess

from .common import CFG_FILE, get_metalinks, get_output


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
        "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/cmip5/MRI/rcp85/fx/atmos/r0i0p0/sftlf/"
        "sftlf_fx_MRI-CGCM3_rcp85_r0i0p0.nc"
    )
    fn2 = (
        "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/cmip5/MRI/rcp85/fx/atmos/r0i0p0/orog/"
        "orog_fx_MRI-CGCM3_rcp85_r0i0p0.nc"
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


"""
# This doesn't work yet.
@pytest.mark.online
def test_bad_link():
    client = client_for(
        Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE)
    )
    fn = "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/cmip5/bad_link.nc"
    datainputs = (
        f"resource=files@xlink:href={fn};"
        "lat=45.0;"
        "lon=150.0;"
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={datainputs}"
    )
    print(resp.response)
    assert "NetCDF: file not found" in resp.response.decode()
"""
