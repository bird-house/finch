import xarray as xr
import finch
from tests.utils import wps_input_file, wps_literal_input, execute_process
from finch.processes import make_xclim_indicator_process


def _get_output_standard_name(process_identifier):
    for p in finch.processes.processes:
        if p.identifier == process_identifier:
            return p.xci.standard_name


def test_tg_mean(client, tas_dataset):
    identifier = "tg_mean"
    inputs = [wps_input_file("tas", tas_dataset)]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds.tg_mean.standard_name == _get_output_standard_name(identifier)


def test_heat_wave_frequency(client, tasmin_dataset, tasmax_dataset):
    identifier = "heat_wave_frequency"
    inputs = [
        wps_input_file("tasmax", tasmax_dataset),
        wps_input_file("tasmin", tasmin_dataset),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds.heat_wave_frequency.standard_name == _get_output_standard_name(identifier)


def test_heat_wave_index(client, tasmax_dataset):
    identifier = "heat_wave_index"
    inputs = [
        wps_input_file("tasmax", tasmax_dataset),
        wps_literal_input("thresh", "30 degC"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds["heat_wave_index"].standard_name == _get_output_standard_name(identifier)
