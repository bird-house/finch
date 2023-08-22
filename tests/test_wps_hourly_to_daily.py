from pathlib import Path

import numpy as np
import xarray as xr

from _utils import execute_process, wps_input_file, wps_literal_input


def test_wps_hourly_to_daily(client, hourly_dataset):
    identifier = "hourly_to_daily"
    inputs = [
        wps_input_file("resource", hourly_dataset),
        wps_literal_input("reducer", "sum"),
        wps_literal_input("missing", "any"),
        wps_literal_input("output_name", "quotidien"),
    ]
    outputs = execute_process(client, identifier, inputs)
    assert Path(outputs[0]).stem == "quotidien"
    with xr.open_dataset(outputs[0]) as ds:
        assert ds.pr.attrs["cell_methods"].endswith(" time: sum within days")
        assert ds.pr.isel(time=0).isnull()
        assert ds.pr.isel(time=1) == np.sum(np.arange(24, 48))
