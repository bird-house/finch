import numpy as np
import pytest
from pywps import Service
from pywps.tests import assert_response_success, client_for
import xarray as xr
from urllib.parse import quote_plus

from finch.processes import HourlyToDailyProcess
from . utils import execute_process, wps_input_file, wps_literal_input
from xclim.sdba.utils import ADDITIVE, MULTIPLICATIVE
from xclim.core.calendar import convert_calendar
from .common import CFG_FILE, get_output


def test_wps_hourly_to_daily(client, hourly_dataset):
    identifier = "hourly_to_daily"
    inputs = [
        wps_input_file("resource", hourly_dataset),
        wps_literal_input("reducer", "sum"),
        wps_literal_input("missing", "any"),
    ]
    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        assert ds.pr.attrs["cell_methods"].endswith(" time: sum")
        assert ds.pr.isel(time=0).isnull()
