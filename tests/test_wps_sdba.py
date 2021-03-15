from pathlib import Path
import collections
import numpy as np
import pandas as pd
import pytest
from pywps import Service
from pywps.tests import assert_response_success, client_for
import xarray as xr

from finch.processes import EmpiricalQuantileMappingProcess
from xclim.sdba.utils import (
    ADDITIVE,
    MULTIPLICATIVE)
from .common import CFG_FILE, get_output


@pytest.mark.parametrize("kind,name", [(ADDITIVE, "tas"), (MULTIPLICATIVE, "pr")])
def test_wps_empirical_quantile_mapping(netcdf_sdba_ds, kind, name):
    client = client_for(Service(processes=[EmpiricalQuantileMappingProcess()], cfgfiles=CFG_FILE))

    u, sdba_ds = netcdf_sdba_ds

    datainputs = (
        f"ref=files@xlink:href=file://{sdba_ds[f'qdm_{name}_ref']};"
        f"hist=files@xlink:href=file://{sdba_ds[f'qdm_{name}_hist']};"
        f"sim=files@xlink:href=file://{sdba_ds[f'qdm_{name}_hist']};"
        "group=time;"
        f"kind={kind};"
        "nquantiles=10;"
        "interp=linear;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=empirical_quantile_mapping&datainputs={datainputs}"
    )
    print(resp.response)
    assert_response_success(resp)
    out = get_output(resp.xml)
    p = xr.open_dataset(out["output"][6:])
    middle = (u > 1e-2) * (u < 0.99)
    np.testing.assert_array_almost_equal(p[middle], sdba_ds[f'qdm_{name}_ref'][middle], 1)




