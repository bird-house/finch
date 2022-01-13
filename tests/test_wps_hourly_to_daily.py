import numpy as np
import xarray as xr
from . utils import execute_process, wps_input_file, wps_literal_input


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
        assert ds.pr.isel(time=1) == np.sum(np.arange(24, 48))
