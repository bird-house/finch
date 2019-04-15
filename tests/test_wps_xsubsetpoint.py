from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, CFG_FILE
from finch.processes import SubsetGridPointProcess
import xarray as xr


def test_wps_xsubsetpoint(tas_data_set):
    client = client_for(Service(processes=[SubsetGridPointProcess()], cfgfiles=CFG_FILE))

    datainputs = "resource=files@xlink:href=file://{fn};"\
        "lat={lat};"\
        "lon={lon};"\
        "y0={y0};"\
        "y1={y1};".format(fn=tas_data_set, lat=2., lon=3., y0=2000, y1=2003)

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset_gridpoint&datainputs={}".format(
            datainputs))

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out['output'][6:])
    assert ds.lat == 2
    assert ds.lon == 3
