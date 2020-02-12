from finch.processes.wps_xclim_indices import XclimIndicatorBase
from inspect import signature

import xarray as xr
import xclim

import finch
import finch.processes
from finch.processes.base import make_xclim_indicator_process
from tests.utils import execute_process, wps_input_file, wps_literal_input


def _get_output_standard_name(process_identifier):
    for p in finch.processes.processes:
        if p.identifier == process_identifier:
            return p.xci.standard_name


def test_indicators_processes_discovery():
    indicators = finch.processes.get_indicators(xclim.atmos)
    indicator_names = [i.identifier for i in indicators]
    processes = [
        make_xclim_indicator_process(ind, "Process", XclimIndicatorBase)
        for ind in indicators
    ]
    for name, indicator, process in zip(indicator_names, indicators, processes):
        assert name == process.identifier
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
        "freq": "YS",
        "window": "3",
    }
    keep_defaults = ["thresh", "thresh_tasmin", "thresh_tasmax"]

    # Todo: remove me when xclim.run_length.first_run_ufunc is fixed
    processes = [p for p in processes if p.identifier != "freshet_start"]

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
