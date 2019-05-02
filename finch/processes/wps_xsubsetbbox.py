from pywps import LiteralInput, ComplexInput, ComplexOutput, FORMATS
from xclim.utils import subset_bbox
from pathlib import Path
from pywps.inout.outputs import MetaFile, MetaLink4
from .base import FinchProcess
import logging


LOGGER = logging.getLogger("PYWPS")


class SubsetBboxProcess(FinchProcess):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "NetCDF resource",
                abstract="NetCDF files, can be OPEnDAP urls.",
                max_occurs=1,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            LiteralInput(
                "lon0",
                "Minimum longitude",
                abstract="Minimum longitude.",
                data_type="float",
                default=0,
                min_occurs=0,
            ),
            LiteralInput(
                "lon1",
                "Maximum longitude",
                abstract="Maximum longitude.",
                data_type="float",
                default=360,
                min_occurs=0,
            ),
            LiteralInput(
                "lat0",
                "Minimum latitude",
                abstract="Minimum latitude.",
                data_type="float",
                default=-90,
                min_occurs=0,
            ),
            LiteralInput(
                "lat1",
                "Maximum latitude",
                abstract="Maximum latitude.",
                data_type="float",
                default=90,
                min_occurs=0,
            ),
            # LiteralInput('dt0',
            #              'Initial datetime',
            #              abstract='Initial datetime for temporal subsetting. Defaults to first date in file.',
            #              data_type='dateTime',
            #              default=None,
            #              min_occurs=0,
            #              max_occurs=1),
            # LiteralInput('dt1',
            #              'Final datetime',
            #              abstract='Final datetime for temporal subsetting. Defaults to last date in file.',
            #              data_type='dateTime',
            #              default=None,
            #              min_occurs=0,
            #              max_occurs=1),
            LiteralInput(
                "y0",
                "Initial year",
                abstract="Initial year for temporal subsetting. Defaults to first year in file.",
                data_type="integer",
                default=None,
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "y1",
                "Final year",
                abstract="Final year for temporal subsetting. Defaults to last year in file.",
                data_type="integer",
                default=None,
                min_occurs=0,
                max_occurs=1,
            ),
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

        super(SubsetBboxProcess, self).__init__(
            self._handler,
            identifier="subset_bbox",
            title="Subset",
            version="0.1",
            abstract=(
                "Return the data for which grid cells intersect the "
                "bounding box for each input dataset as well as "
                "the time range selected."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        self.sentry_configure_scope(request)

        self.write_log("Processing started", response, 5)

        metalink = self.subset(request.inputs, response)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["output"].file = metalink.files[0]
        response.outputs["ref"].data = metalink.xml

        return response
