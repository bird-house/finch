import pytest
import os
import numpy as np
from pywps import Service
from pywps.tests import assert_response_success

from finch.tests.common import client_for, TESTS_HOME
from finch.processes.wps_xclim_indices import tmmean

from xclim.testing.common import tas_series
import tempfile

cfgfiles = os.path.join(TESTS_HOME, 'test.cfg')



@pytest.mark.online
def test_wps_wordcount(tas_series):
    ts = tas_series(np.arange(360))
    fn = tempfile.mktemp('.nc', 'tas')
    ts.to_netcdf(fn)

    client = client_for(Service(processes=[tmmean], cfgfiles=cfgfiles))
    datainputs = "tas=files@xlink:href=file://{tas};freq=YS".format(tas=fn)

    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='tmmean',
        datainputs=datainputs)

    assert_response_success(resp)
