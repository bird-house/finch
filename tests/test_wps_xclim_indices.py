from finch.processes.wps_xclim_indices import XclimIndicatorBase
from inspect import signature

import xarray as xr
import pandas as pd

import finch
import finch.processes
from finch.processes.wps_base import make_xclim_indicator_process
from tests.utils import execute_process, wps_input_file, wps_literal_input
from pathlib import Path


def _get_output_standard_name(process_identifier):
    for p in finch.processes.processes:
        if p.identifier == process_identifier:
            return p.xci.standard_name


def test_indicators_processes_discovery():
    for indicator in finch.processes.indicators:
        process = make_xclim_indicator_process(indicator, "Process", XclimIndicatorBase)
        assert indicator.identifier == process.identifier
        sig = signature(indicator.compute)
        # the phase parameter is set by a partial function in xclim, so there is
        # no input necessary from the user in the WPS process
        parameters = [k for k in sig.parameters.keys() if k != "phase"]
        for parameter, input_ in zip(parameters, process.inputs):
            assert parameter == input_.identifier


def test_processes(client, netcdf_datasets):
    """Run a dummy calculation for every process, keeping some default parameters."""
    indicators = finch.processes.indicators
    processes = [
        make_xclim_indicator_process(ind, "Process", XclimIndicatorBase)
        for ind in indicators
    ]
    literal_inputs = {
        "freq": "MS",
        "window": "3",
    }
    keep_defaults = ["thresh", "thresh_tasmin", "thresh_tasmax"]

    attrs = xr.open_dataset(list(netcdf_datasets.values())[0], decode_times=False).attrs

    for process in processes:
        inputs = []
        for process_input in process.inputs:
            name = process_input.identifier
            if name in netcdf_datasets.keys():
                inputs.append(wps_input_file(name, netcdf_datasets[name]))
            elif name in literal_inputs.keys():
                inputs.append(wps_literal_input(name, literal_inputs[name]))
            elif name in keep_defaults:
                pass
            else:
                raise NotImplementedError
        outputs = execute_process(client, process.identifier, inputs)
        ds = xr.open_dataset(outputs[0])
        output_variable = list(ds.data_vars)[0]

        assert getattr(ds, output_variable).standard_name == process.xci.standard_name

        model = attrs["driving_model_id"]
        experiment = attrs["driving_experiment_id"].replace(",", "+")
        ensemble = (
            f"r{attrs['driving_realization']}"
            f"i{attrs['driving_initialization_method']}"
            f"p{attrs['driving_physics_version']}"
        )
        date_start = pd.to_datetime(str(ds.time[0].values))
        date_end = pd.to_datetime(str(ds.time[-1].values))

        expected = f"{output_variable}_{model}_{experiment}_{ensemble}_{date_start:%Y%m%d}-{date_end:%Y%m%d}.nc"
        assert Path(outputs[0]).name == expected


def test_heat_wave_frequency_window_thresh_parameters(client, netcdf_datasets):
    identifier = "heat_wave_frequency"
    inputs = [
        wps_input_file("tasmax", netcdf_datasets["tasmax"]),
        wps_input_file("tasmin", netcdf_datasets["tasmin"]),
        wps_literal_input("window", "3"),
        wps_literal_input("thresh_tasmin", "20 degC"),
        wps_literal_input("thresh_tasmax", "25 degC"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds.heat_wave_frequency.standard_name == _get_output_standard_name(identifier)


def test_heat_wave_index_thresh_parameter(client, netcdf_datasets):
    identifier = "heat_wave_index"
    inputs = [
        wps_input_file("tasmax", netcdf_datasets["tasmax"]),
        wps_literal_input("thresh", "30 degC"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds["heat_wave_index"].standard_name == _get_output_standard_name(identifier)
