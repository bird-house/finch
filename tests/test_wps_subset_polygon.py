from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, CFG_FILE
from finch.processes import SubsetPolygonProcess
import xarray as xr
from pathlib import Path
import xclim
import geojson

TESTS_DATA = Path(xclim.__file__).parent.parent / 'tests' / 'testdata'

poly = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [[0, 0], [2.5, 0], [2.5, 2.5], [0, 2.5]]
        ]
    }
    }


def test_wps_xsubsetpoint(tas_dataset):
    client = client_for(Service(processes=[SubsetPolygonProcess()], cfgfiles=CFG_FILE))

    datainputs = "resource=files@xlink:href=file://{fn};"\
        "shape={shape};"\
        "start={y0};".format(fn=tas_dataset, shape=geojson.dumps(poly), y0='2000')

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset_polygon&datainputs={}".format(
            datainputs))
    print(resp.response)
    assert_response_success(resp)

