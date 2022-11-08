# noqa: D100
import logging

from pywps import FORMATS, ComplexInput, ComplexOutput

from . import wpsio
from .subset import common_subset_handler, finch_average_shape
from .wps_base import FinchProcess

LOGGER = logging.getLogger("PYWPS")


class AveragePolygonProcess(FinchProcess):
    """Subset a NetCDF file using a polygon contour."""

    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "NetCDF resource",
                abstract="NetCDF files, can be OPEnDAP urls.",
                max_occurs=1000,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            wpsio.shape,
            wpsio.tolerance,
            wpsio.start_date,
            wpsio.end_date,
            wpsio.variable_any,
        ]

        outputs = [
            ComplexOutput(
                "output",
                "netCDF output",
                as_reference=True,
                supported_formats=[FORMATS.NETCDF],
            ),
            wpsio.output_metalink,
        ]

        super().__init__(
            self._handler,
            identifier="average_polygon",
            title="Average over one or more polygons",
            version="0.1",
            abstract=(
                "Return the average of the data within each polygons, "
                "taking into account partial overlaps and holes, "
                "for each input dataset as well as the time range selected."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {
            "start": 5,
            "done": 99,
        }

    def _handler(self, request, response):
        return common_subset_handler(self, request, response, finch_average_shape)
