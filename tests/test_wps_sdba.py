from urllib.parse import quote_plus

import numpy as np
import pytest
import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for
from xclim.core.calendar import convert_calendar
from xclim.sdba.utils import ADDITIVE, MULTIPLICATIVE

from _common import CFG_FILE, get_output
from finch.processes import EmpiricalQuantileMappingProcess


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
    p = xr.open_dataset(out["output"][7:])[name]

    uc = convert_calendar(u, "noleap")
    middle = ((uc > 1e-2) * (uc < 0.99)).data

    ref = xr.open_dataset(sdba_ds[f"qdm_{name}_ref"])[name]
    refc = convert_calendar(ref, "noleap")
    np.testing.assert_allclose(p[middle], refc[middle], rtol=0.03)
