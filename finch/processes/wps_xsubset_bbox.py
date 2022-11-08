# noqa: D100
import logging

from pywps import FORMATS, ComplexInput, ComplexOutput

from . import wpsio
from .subset import common_subset_handler, finch_subset_bbox
from .wps_base import FinchProcess

LOGGER = logging.getLogger("PYWPS")


class SubsetBboxProcess(FinchProcess):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "NetCDF resource",
                abstract="NetCDF files, can be OPEnDAP urls.",
                max_occurs=1000,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            wpsio.lon0,
            wpsio.lon1,
            wpsio.lat0,
            wpsio.lat1,
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
            identifier="subset_bbox",
            title="Subset with bounding box",
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

        self.status_percentage_steps = {
            "start": 5,
            "done": 99,
        }

    def _handler(self, request, response):
        return common_subset_handler(self, request, response, finch_subset_bbox)
