import pytest

from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, CFG_FILE
from finch.processes import SubsetBboxProcess
import xarray as xr
import numpy as np
from pathlib import Path


def test_wps_subsetbbox(tas_dataset):
    client = client_for(Service(processes=[SubsetBboxProcess()], cfgfiles=CFG_FILE))

    datainputs = "resource=files@xlink:href=file://{fn};" \
                 "lat0={lat0};" \
                 "lon0={lon0};" \
                 "lat1={lat1};" \
                 "lon1={lon1};" \
                 "start_date={y0};".format(fn=tas_dataset, lat0=2., lon0=3., lat1=4, lon1=5, y0='2000')

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset_bbox&datainputs={}".format(
            datainputs))

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out['output'][6:])
    np.testing.assert_array_equal(ds.lat, [2, 3, 4])
    np.testing.assert_array_equal(ds.lon, [3, 4])
