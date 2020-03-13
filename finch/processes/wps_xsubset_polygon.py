import logging
from threading import Lock

from pywps import ComplexInput, ComplexOutput, FORMATS
from pywps.inout.outputs import MetaLink4
from xclim.subset import subset_shape

from . import wpsio
from .wps_base import FinchProcess
from .subset import common_subset_handler, finch_subset_shape

LOGGER = logging.getLogger("PYWPS")


class SubsetPolygonProcess(FinchProcess):
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

        super(SubsetPolygonProcess, self).__init__(
            self._handler,
            identifier="subset_polygon",
            title="Subset with one or more polygons",
            version="0.1",
            abstract=(
                "Return the data for which grid cells center are within the "
                "polygon for each input dataset as well as "
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

    def subset(
        self, wps_inputs, response, start_percentage=10, end_percentage=85, threads=1
    ) -> MetaLink4:
        shape = self.get_shape(wps_inputs)
        start = self.get_input_or_none(wps_inputs, "start_date")
        end = self.get_input_or_none(wps_inputs, "end_date")
        variables = [r.data for r in wps_inputs.get("variable", [])]

        n_files = len(wps_inputs["resource"])
        count = 0

        lock = Lock()

        def _subset_function(resource):
            nonlocal count

            # if not subsetting by time, it's not necessary to decode times
            time_subset = start is not None or end is not None
            dataset = self.try_opendap(resource, decode_times=time_subset)

            with lock:
                count += 1
                percentage = start_percentage + int(
                    (count - 1) / n_files * (end_percentage - start_percentage)
                )
                self.write_log(
                    f"Subsetting file {count} of {n_files}",
                    response=response,
                    percentage=percentage,
                )

            dataset = dataset[variables] if variables else dataset
            return subset_shape(dataset, shape, start_date=start, end_date=end)

        metalink = self.subset_resources(
            wps_inputs["resource"], _subset_function, threads=threads
        )

        return metalink

    def _handler(self, request, response):
        return common_subset_handler(self, request, response, finch_subset_shape)
