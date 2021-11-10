"""Module storing inputs and outputs used in multiple processes. """

import json
from copy import deepcopy
from typing import Union

from pywps import FORMATS, ComplexInput, ComplexOutput, LiteralInput
from pywps.inout.literaltypes import AnyValue
from xclim.core.options import (
    CHECK_MISSING,
    CF_COMPLIANCE,
    DATA_VALIDATION,
    MISSING_METHODS,
    MISSING_OPTIONS,
    OPTIONS
)

from .constants import ALL_24_MODELS, ALLOWED_MODEL_NAMES
from .utils import PywpsInput, PywpsOutput


def copy_io(
    io: Union[PywpsInput, PywpsOutput], **kwargs
) -> Union[PywpsInput, PywpsOutput]:
    """Creates a new input or output with modified parameters.

    Use this if you want one of the inputs in this file, but want to modify it.

    This is necessary because if we modify the input or output directly,
    every other place where this input is used would be affected.
    """
    new_io = deepcopy(io)
    for k, v in kwargs.items():
        setattr(new_io, k, v)
    return new_io


start_date = LiteralInput(
    "start_date",
    "Initial date",
    abstract="Initial date for temporal subsetting. Can be expressed as year (%Y), year-month (%Y-%m) or "
    "year-month-day(%Y-%m-%d). Defaults to first day in file.",
    data_type="string",
    default=None,
    min_occurs=0,
    max_occurs=1,
)

end_date = LiteralInput(
    "end_date",
    "Final date",
    abstract="Final date for temporal subsetting. Can be expressed as year (%Y), year-month (%Y-%m) or "
    "year-month-day(%Y-%m-%d). Defaults to last day in file.",
    data_type="string",
    default=None,
    min_occurs=0,
    max_occurs=1,
)

lon = LiteralInput(
    "lon",
    "Longitude",
    abstract="Longitude coordinate. Accepts a comma separated list of floats for multiple grid cells.",
    data_type="string",
    min_occurs=1,
    max_occurs=100,
)

lat = LiteralInput(
    "lat",
    "Latitude",
    abstract="Latitude coordinate. Accepts a comma separated list of floats for multiple grid cells.",
    data_type="string",
    min_occurs=1,
    max_occurs=100,
)

lon0 = LiteralInput(
    "lon0",
    "Minimum longitude",
    abstract="Minimum longitude.",
    data_type="float",
    default=0,
    min_occurs=0,
)

lon1 = LiteralInput(
    "lon1",
    "Maximum longitude",
    abstract="Maximum longitude.",
    data_type="float",
    default=360,
    min_occurs=0,
)

lat0 = LiteralInput(
    "lat0",
    "Minimum latitude",
    abstract="Minimum latitude.",
    data_type="float",
    default=-90,
    min_occurs=0,
)

lat1 = LiteralInput(
    "lat1",
    "Maximum latitude",
    abstract="Maximum latitude.",
    data_type="float",
    default=90,
    min_occurs=0,
)

average = LiteralInput(
    "average",
    "Perform spatial average.",
    abstract="Whether to average over spatial dimensions or not. Averaging is done before the ensemble percentiles.",
    data_type="boolean",
    default=False,
    min_occurs=0,
)

variable = LiteralInput(
    "variable",
    "NetCDF Variable",
    abstract="Name of the variable in the NetCDF file.",
    data_type="string",
    default=None,
    min_occurs=0,
    allowed_values=["tasmin", "tasmax", "pr"],
)

variable_any = copy_io(variable, any_value=True, allowed_values=[AnyValue])

dataset_name = LiteralInput(
    "dataset_name",
    "Dataset name",
    abstract="Name of the dataset from which to get netcdf files for inputs.",
    data_type="string",
    default=None,
    min_occurs=0,
    allowed_values=["bccaqv2"],
)

rcp = LiteralInput(
    "rcp",
    "RCP Scenario",
    abstract="Representative Concentration Pathway (RCP)",
    data_type="string",
    default=None,
    min_occurs=0,
    allowed_values=["rcp26", "rcp45", "rcp85"],
)

models = LiteralInput(
    "models",
    "Models to include in ensemble",
    abstract=(
        "When calculating the ensemble, include only these models. By default, all 24 models are used."
    ),
    data_type="string",
    default=ALL_24_MODELS,
    min_occurs=0,
    max_occurs=1000,
    allowed_values=ALLOWED_MODEL_NAMES,
)

shape = ComplexInput(
    "shape",
    "Polygon shape",
    abstract="Polygon contour, as a geojson string or as a zipped ShapeFile.",
    supported_formats=[FORMATS.GEOJSON, FORMATS.SHP],
    min_occurs=1,
    max_occurs=1,
)

ensemble_percentiles = LiteralInput(
    "ensemble_percentiles",
    "Ensemble percentiles",
    abstract=(
        "Ensemble percentiles to calculate for input climate simulations. "
        "Accepts a comma separated list of integers."
    ),
    data_type="string",
    default="10,50,90",
    min_occurs=0,
)

check_missing = LiteralInput(
    "check_missing",
    "Missing value handling method",
    abstract="Method used to determine which aggregations should be considered missing.",
    data_type="string",
    default=OPTIONS[CHECK_MISSING],
    allowed_values=list(MISSING_METHODS.keys()),
    min_occurs=0,
)


missing_options = ComplexInput(
    "missing_options",
    "Missing method parameters",
    abstract="JSON representation of dictionary of missing method parameters.",
    default=json.dumps(OPTIONS[MISSING_OPTIONS][OPTIONS[CHECK_MISSING]]),
    supported_formats=[FORMATS.JSON],
    min_occurs=0,
)


cf_compliance = LiteralInput(
    "cf_compliance",
    "Strictness level for CF-compliance input checks.",
    abstract="Whether to log, warn or raise when inputs have non-CF-compliant attributes.",
    data_type="string",
    default=OPTIONS[CF_COMPLIANCE],
    allowed_values=['log', 'warn', 'raise'],
    min_occurs=0,
)


data_validation = LiteralInput(
    "data_validation",
    "Strictness level for data validation input checks.",
    abstract="Whether to log, warn or raise when inputs fail data validation checks.",
    data_type="string",
    default=OPTIONS[DATA_VALIDATION],
    allowed_values=['log', 'warn', 'raise'],
    min_occurs=0,
)


output_format_netcdf_csv = LiteralInput(
    "output_format",
    "Output format choice",
    abstract="Choose in which format you want to recieve the result",
    data_type="string",
    allowed_values=["netcdf", "csv"],
    default="netcdf",
    min_occurs=0,
)

output_netcdf_zip = ComplexOutput(
    "output",
    "Result",
    abstract=("The format depends on the 'output_format' input parameter."),
    as_reference=True,
    supported_formats=[FORMATS.NETCDF, FORMATS.ZIP],
)

output_netcdf_csv = copy_io(
    output_netcdf_zip, supported_formats=[FORMATS.NETCDF, FORMATS.TEXT]
)

output_log = ComplexOutput(
    "output_log",
    "Logging information",
    abstract="Collected logs during process run.",
    as_reference=True,
    supported_formats=[FORMATS.TEXT],
)

output_metalink = ComplexOutput(
    "ref",
    "Link to all output files",
    abstract="Metalink file storing all references to output files.",
    as_reference=False,
    supported_formats=[FORMATS.META4],
)

tolerance = LiteralInput(
    "tolerance",
    "Tolerance",
    abstract=(
        "The polygon tolerance in degrees."
        "High-resolution polygons are simplified to this tolerance "
        "in order to speed up the averaging. Put 0 to disable that simplification."
    ),
    data_type="float",
    default=0.001,
    min_occurs=0,
)

xclim_common_options = [
    check_missing,
    missing_options,
    cf_compliance,
    data_validation,
]
