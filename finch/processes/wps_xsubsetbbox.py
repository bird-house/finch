from pywps import LiteralInput, ComplexInput, ComplexOutput, FORMATS
from pywps.inout.outputs import MetaLink4
from xclim.subset import subset_bbox

from finch.processes.subset import SubsetProcess
import logging
from contextlib import suppress


LOGGER = logging.getLogger("PYWPS")


class SubsetBboxProcess(SubsetProcess):
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

    def subset(self, wps_inputs, response, start_percentage=10, end_percentage=85) -> MetaLink4:
        lon0 = wps_inputs["lon0"][0].data
        lon1 = wps_inputs["lon1"][0].data
        lat0 = wps_inputs["lat0"][0].data
        lat1 = wps_inputs["lat1"][0].data
        # dt0 = wps_inputs['dt0'][0].data or None
        # dt1 = wps_inputs['dt1'][0].data or None
        y0, y1 = None, None
        with suppress(KeyError):
            y0 = wps_inputs["y0"][0].data
        with suppress(KeyError):
            y1 = wps_inputs["y1"][0].data
        variables = [r.data for r in wps_inputs.get("variable", [])]

        n_files = len(wps_inputs["resources"])
        count = 0

        def _subset_function(dataset):
            nonlocal count

            percentage = start_percentage + int(count / n_files * (end_percentage - start_percentage))
            self.write_log(f"Processing file {count + 1} of {n_files}", response, percentage)
            count += 1

            dataset = dataset[variables] if variables else dataset
            return subset_bbox(
                dataset, lon_bnds=[lon0, lon1], lat_bnds=[lat0, lat1], start_yr=y0, end_yr=y1
            )

        metalink = self.subset_resources(wps_inputs["resources"], _subset_function)

        return metalink

    def _handler(self, request, response):
        self.write_log("Processing started", response, 5)

        metalink = self.subset(request.inputs, response)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["output"].file = metalink.files[0].file
        response.outputs["ref"].data = metalink.xml

        return response
