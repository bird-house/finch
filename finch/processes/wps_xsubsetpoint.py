from pywps import ComplexInput, ComplexOutput, FORMATS, LiteralInput

from .base import FinchProcess
from .subset import finch_subset_gridpoint
from .utils import make_metalink_output, write_log
from .wpsio import end_date, lat, lon, start_date


class SubsetGridPointProcess(FinchProcess):
    """Subset a NetCDF file grid cells using a list of coordinates."""

    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "NetCDF resource",
                abstract="NetCDF files, can be OPEnDAP urls.",
                max_occurs=1000,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            lon,
            lat,
            start_date,
            end_date,
            LiteralInput(
                "variable",
                "Variable",
                abstract=(
                    "Name of the variable in the NetCDF file."
                    "If not provided, all variables will be subsetted."
                ),
                data_type="string",
                default=None,
                min_occurs=0,
            ),
        ]

        outputs = [
            ComplexOutput(
                "output",
                "netCDF output",
                as_reference=True,
                supported_formats=[FORMATS.NETCDF],
            ),
            ComplexOutput(
                "ref",
                "Link to all output files",
                abstract="Metalink file storing all references to output file.",
                as_reference=False,
                supported_formats=[FORMATS.META4],
            ),
        ]

        super().__init__(
            self._handler,
            identifier="subset_gridpoint",
            title="Subset with a grid point",
            version="0.2",
            abstract=(
                "Return the data for which grid cells includes the "
                "point coordinates for each input dataset as well as "
                "the time range selected."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        write_log(self, "Processing started")

        output_files = finch_subset_gridpoint(self, request.inputs)
        metalink = make_metalink_output(self, output_files)

        response.outputs["output"].file = metalink.files[0].file
        response.outputs["ref"].data = metalink.xml

        write_log(self, "Processing finished successfully")

        return response
