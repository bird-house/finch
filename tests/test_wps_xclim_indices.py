import pytest

from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, CFG_FILE
from finch.processes import UnivariateXclimIndicatorProcess
from xclim.temperature import tmmean
import xarray as xr
from pathlib import Path


def test_wps_xclim_indices(tas_data_set):
    client = client_for(Service(processes=[UnivariateXclimIndicatorProcess(tmmean)], cfgfiles=CFG_FILE))

    datainputs = "tas=files@xlink:href=file://{fn};" \
                 "freq={freq}".format(fn=tas_data_set,
                                      freq='MS')

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=tmmean&datainputs={}".format(
            datainputs))

    assert_response_success(resp)
    out = get_output(resp.xml)
    p = Path(out['output_netcdf'])
    fn = Path('/').joinpath(*p.parts[1:])
    ds = xr.open_dataset(fn)
    assert ds.tmmean.standard_name == 'air_temperature'
