"""Module storing inputs and outputs used in multiple processes. """

from pywps import LiteralInput

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
)

lat = LiteralInput(
    "lat",
    "Latitude",
    abstract="Latitude coordinate. Accepts a comma separated list of floats for multiple grid cells.",
    data_type="string",
    min_occurs=1,
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

rcp = LiteralInput(
    "rcp",
    "RCP Scenario",
    abstract="Representative Concentration Pathway (RCP)",
    data_type="string",
    default=None,
    min_occurs=0,
    allowed_values=["rcp26", "rcp45", "rcp85"],
)

output_netcdf_csv = LiteralInput(
    "output_format",
    "Output format choice",
    abstract="Choose in which format you want to recieve the result",
    data_type="string",
    allowed_values=["netcdf", "csv"],
    default="netcdf",
)

