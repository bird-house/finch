from owslib.wps import WPSExecution

import pytest
from pywps import Service
from pywps.tests import client_for, assert_response_success
from xclim import temperature
import xarray as xr
from pywps import get_ElementMakerForVersion

import finch
from .common import get_output, CFG_FILE
from finch.processes import make_xclim_indicator_process


VERSION = "1.0.0"

WPS, OWS = get_ElementMakerForVersion(VERSION)


def _wps_input_file(identifier, filename):
    return WPS.Input(
        OWS.Identifier(identifier),
        WPS.Reference(
            WPS.Body("request body"),
            {"{http://www.w3.org/1999/xlink}href": "file://" + filename},
            method="POST",
        ),
    )


def _wps_literal_input(identifier, value):
    return WPS.Input(OWS.Identifier(identifier), WPS.Data(WPS.LiteralData(value)))


@pytest.fixture(scope="module")
def client():
    return client_for(Service(processes=finch.processes.processes, cfgfiles=CFG_FILE))


def _execute_process(client, identifier, inputs) -> xr.Dataset:
    """Execute a process using the test client, and return the 'output_netcdf' output as an xarray.Dataset"""
    request_doc = WPS.Execute(
        OWS.Identifier(identifier), WPS.DataInputs(*inputs), version="1.0.0"
    )
    response = client.post_xml(doc=request_doc)
    assert_response_success(response)

    execution = WPSExecution()
    execution.parseResponse(response.xml)

    ds = _get_output_dataset(execution)

    return ds


def _get_output_dataset(execution):
    ds = None
    for output in execution.processOutputs:
        if output.identifier == "output_netcdf":
            path = output.reference.replace("file://", "")
            ds = xr.open_dataset(path)
    return ds


def _get_output_standard_name(process_identifier):
    for p in finch.processes.processes:
        if p.identifier == process_identifier:
            return p.xci.standard_name


def test_tg_mean(client, tas_dataset):
    identifier = "tg_mean"
    inputs = [_wps_input_file("tas", tas_dataset)]
    ds = _execute_process(client, identifier, inputs)

    assert ds.tg_mean.standard_name == _get_output_standard_name(identifier)


def test_heat_wave_frequency(client, tasmin_dataset, tasmax_dataset):
    identifier = "heat_wave_frequency"
    inputs = [
        _wps_input_file("tasmax", tasmax_dataset),
        _wps_input_file("tasmin", tasmin_dataset),
    ]
    ds = _execute_process(client, identifier, inputs)

    assert ds.heat_wave_frequency.standard_name == _get_output_standard_name(identifier)


def test_heat_wave_index(client, tasmax_dataset):
    identifier = "hwi_{thresh}"
    inputs = [
        _wps_input_file("tasmax", tasmax_dataset),
        _wps_literal_input("thresh", "30"),
    ]
    ds = _execute_process(client, identifier, inputs)

    assert ds.hwi_30.standard_name == _get_output_standard_name(identifier)
