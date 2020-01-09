"""Module storing inputs and outputs used in multiple processes. """

from pywps import LiteralInput, ComplexInput, FORMATS

start_date = LiteralInput(
    "start_date",
    "Initial date",
    abstract="Initial date for temporal subsetting. Can be expressed as year (%Y), year-month (%Y-%m) or "
             "year-month-day(%Y-%m-%d). Defaults to first day in file.",
    data_type="string",
    default=None,
    min_occurs=0,
    max_occurs=1,)

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

shape = ComplexInput(
    "shape",
    "Polygon shape",
    abstract="Polygon contour",
    supported_formats=[FORMATS.GEOJSON,],
    min_occurs=1,
    max_occurs=1
)
