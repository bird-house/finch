from pywps import get_ElementMakerForVersion
from pathlib import Path

import xarray as xr
from owslib.wps import WPSExecution
from pywps.app.exceptions import ProcessError
from pywps.tests import assert_response_success


VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)


def shapefile_zip():
    return (Path(__file__).parent / "data" / "shapefile.zip").as_posix()


def mock_local_datasets(monkeypatch, filenames=None):
    """Mock the get_bccaqv2_local_files_datasets function

    Datasets are of the following format:

    >>> ds
    <xarray.Dataset>
    Dimensions:  (lat: 12, lon: 12, time: 100)
    Coordinates:
    * lon      (lon) float64 -73.46 -73.38 -73.29 -73.21 ... -72.71 -72.63 -72.54
    * lat      (lat) float64 45.54 45.62 45.71 45.79 ... 46.21 46.29 46.37 46.46
    * time     (time) object 1950-01-01 12:00:00 ... 1950-04-10 12:00:00
    Data variables:
        tasmax   (time, lat, lon) float32 ...
    """
    from pywps.configuration import CONFIG
    from finch.processes import ensemble_utils

    CONFIG.set("finch", "dataset_bccaqv2", "/mock_local/path")

    subset_sample = Path(__file__).parent / "data" / "bccaqv2_subset_sample"

    if filenames is None:
        filenames = ["tasmin_subset.nc", "tasmax_subset.nc"]

    test_data = [subset_sample / f for f in filenames]

    monkeypatch.setattr(
        ensemble_utils,
        "get_bccaqv2_local_files_datasets",
        lambda *args, **kwargs: [str(f) for f in test_data],
    )


def wps_input_file(identifier, filename):
    return WPS.Input(
        OWS.Identifier(identifier),
        WPS.Reference(
            WPS.Body("request body"),
            {"{http://www.w3.org/1999/xlink}href": "file://" + str(filename)},
            method="POST",
        ),
    )


def wps_literal_input(identifier, value):
    return WPS.Input(OWS.Identifier(identifier), WPS.Data(WPS.LiteralData(value)))


def execute_process(
    client, identifier, inputs, output_names=("output",)
) -> xr.Dataset:
    """Execute a process using the test client, and return the 'output_netcdf' output as an xarray.Dataset"""
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


def get_outputs(execution, output_names):
    outputs = []
    for output in execution.processOutputs:
        if output.identifier in output_names:
            try:
                outputs.append(output.reference.replace("file://", ""))
            except AttributeError:
                outputs.append(output)
    return outputs
