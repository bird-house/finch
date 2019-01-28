import pytest

from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, CFG_FILE
from finch.processes import SubsetBboxProcess
import xarray as xr
from pathlib import Path


def test_wps_xclim_indices(tas_data_set):
    client = client_for(Service(processes=[SubsetBboxProcess()], cfgfiles=CFG_FILE))

    datainputs = "resource=files@xlink:href=file://{fn};".format(fn=tas_data_set)

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset_bbox&datainputs={}".format(
            datainputs))

    assert_response_success(resp)

