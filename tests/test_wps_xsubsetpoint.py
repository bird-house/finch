from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, get_metalinks, CFG_FILE
from finch.processes import SubsetGridPointProcess
import xarray as xr


def test_wps_xsubsetpoint(tas_dataset):
    client = client_for(Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE))

    datainputs = "resource=files@xlink:href=file://{fn};"\
        "lat={lat};"\
        "lon={lon};"\
        "start={y0};".format(fn=tas_dataset, lat=2., lon=3., y0='2000')

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={}".format(
            datainputs))

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out['output'][6:])
    assert ds.lat == 2
    assert ds.lon == 3


def test_thredds():
    import lxml.etree

    client = client_for(Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE))
    fn1 = "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/cmip5/MRI/rcp85/fx/atmos/r0i0p0" \
          "/sftlf/sftlf_fx_MRI-CGCM3_rcp85_r0i0p0.nc"
    fn2 = "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/cmip5/MRI/rcp85/fx/atmos/r0i0p0/orog" \
          "/orog_fx_MRI-CGCM3_rcp85_r0i0p0.nc"

    datainputs = "resource=files@xlink:href={fn1};" \
        "resource=files@xlink:href={fn2};" \
        "lat={lat};"\
        "lon={lon};".format(fn1=fn1, fn2=fn2, lat=45., lon=150.)

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={}".format(
            datainputs))

    assert_response_success(resp)
    out = get_output(resp.xml)
    links = get_metalinks(lxml.etree.fromstring(out['ref'].encode()))
    assert len(links) == 2
