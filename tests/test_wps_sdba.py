from pathlib import Path
import collections
import numpy as np
import pandas as pd
import pytest
from pywps import Service
from pywps.tests import assert_response_success, client_for
import xarray as xr
from urllib.parse import quote_plus

from finch.processes import EmpiricalQuantileMappingProcess
from xclim.sdba.utils import ADDITIVE, MULTIPLICATIVE
from .common import CFG_FILE, get_output


@pytest.mark.parametrize("kind,name", [(ADDITIVE, "tas"), (MULTIPLICATIVE, "pr")])
def test_wps_empirical_quantile_mapping(netcdf_sdba_ds, kind, name):
    client = client_for(
        Service(processes=[EmpiricalQuantileMappingProcess()], cfgfiles=CFG_FILE)
    )

    sdba_ds, u = netcdf_sdba_ds

    datainputs = (
        f"ref=files@xlink:href=file://{sdba_ds[f'qdm_{name}_ref']};"
        f"hist=files@xlink:href=file://{sdba_ds[f'qdm_{name}_hist']};"
        f"sim=files@xlink:href=file://{sdba_ds[f'qdm_{name}_hist']};"
        "group=time;"
        f"kind={quote_plus(kind)};"
        "nquantiles=50;"
        "interp=linear;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=empirical_quantile_mapping&datainputs={datainputs}"
    )
    print(resp.response)
    assert_response_success(resp)
    out = get_output(resp.xml)
    p = xr.open_dataset(out["output"][6:])[name]
    middle = (u > 1e-2) * (u < 0.99)

    ref = xr.open_dataset(sdba_ds[f"qdm_{name}_ref"])[name]
    np.testing.assert_array_almost_equal(p[middle], ref[middle], 1)
