import numpy as np
import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for

from finch.processes import SubsetBboxProcess

from .common import CFG_FILE, get_output


def test_wps_subsetbbox(netcdf_datasets):
    client = client_for(Service(processes=[SubsetBboxProcess()], cfgfiles=CFG_FILE))

    datainputs = (
        f"resource=files@xlink:href=file://{netcdf_datasets['tas']};"
        "lat0=2;"
        "lon0=3;"
        "lat1=4;"
        "lon1=5;"
        "start_date=2000;"
    )

    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset_bbox&datainputs={datainputs}"
    )

    assert_response_success(resp)
    out = get_output(resp.xml)
    ds = xr.open_dataset(out["output"][6:])
    np.testing.assert_array_equal(ds.lat, [2, 3, 4])
    np.testing.assert_array_equal(ds.lon, [3, 4])
