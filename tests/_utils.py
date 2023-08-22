# noqa: D100
from pathlib import Path

from owslib.wps import WPSExecution
from pywps import get_ElementMakerForVersion
from pywps.app.exceptions import ProcessError
from pywps.tests import assert_response_success

VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)


def shapefile_zip():  # noqa: D103
    return (Path(__file__).parent / "data" / "shapefile.zip").as_posix()


def wps_input_file(identifier, filename):  # noqa: D103
    return WPS.Input(
        OWS.Identifier(identifier),
        WPS.Reference(
            WPS.Body("request body"),
            {"{http://www.w3.org/1999/xlink}href": "file://" + str(filename)},
            method="POST",
        ),
    )


def wps_literal_input(identifier, value):  # noqa: D103
    return WPS.Input(OWS.Identifier(identifier), WPS.Data(WPS.LiteralData(value)))


def execute_process(client, identifier, inputs, output_names=("output",)) -> list:
    """Execute a process using the test client, and return the 'output_netcdf' output as an xarray.Dataset."""
    request_doc = WPS.Execute(
        OWS.Identifier(identifier), WPS.DataInputs(*inputs), version="1.0.0"
    )
    response = client.post_xml(doc=request_doc)
    try:
        assert_response_success(response)
    except AssertionError as e:
        exception = response.xpath("//ows:Exception")[0]
        exception_code = exception.get("exceptionCode")
        message = exception[0].text
        output_message = f"{exception_code}: {message}"
        raise ProcessError(output_message) from e

    execution = WPSExecution()
    execution.parseResponse(response.xml)

    outputs = get_outputs(execution, output_names=output_names)

    return outputs


def get_outputs(execution, output_names):  # noqa: D103
    outputs = []
    for output in execution.processOutputs:
        if output.identifier in output_names:
            try:
                outputs.append(output.reference.replace("file://", ""))
            except AttributeError:
                outputs.append(output)
    return outputs
