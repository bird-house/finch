from pywps import get_ElementMakerForVersion

import xarray as xr
from owslib.wps import WPSExecution
from pywps.tests import assert_response_success


VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)


def wps_input_file(identifier, filename):
    return WPS.Input(
        OWS.Identifier(identifier),
        WPS.Reference(
            WPS.Body("request body"),
            {"{http://www.w3.org/1999/xlink}href": "file://" + filename},
            method="POST",
        ),
    )


def wps_literal_input(identifier, value):
    return WPS.Input(OWS.Identifier(identifier), WPS.Data(WPS.LiteralData(value)))


def execute_process(
    client, identifier, inputs, output_names=("output_netcdf",)
) -> xr.Dataset:
    """Execute a process using the test client, and return the 'output_netcdf' output as an xarray.Dataset"""
    request_doc = WPS.Execute(
        OWS.Identifier(identifier), WPS.DataInputs(*inputs), version="1.0.0"
    )
    response = client.post_xml(doc=request_doc)
    assert_response_success(response)

    execution = WPSExecution()
    execution.parseResponse(response.xml)

    outputs = get_file_outputs(execution, output_names=output_names)

    return outputs


def get_file_outputs(execution, output_names):
    outputs = []
    for output in execution.processOutputs:
        if output.identifier in output_names:
            outputs.append(output.reference.replace("file://", ""))
    return outputs
