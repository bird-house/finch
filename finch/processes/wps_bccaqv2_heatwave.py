import logging
from collections import defaultdict
from typing import List

from xclim.atmos import heat_wave_frequency
from pathlib import Path
from pywps.response.execute import ExecuteResponse
from pywps.app.exceptions import ProcessError
from pywps.app import WPSRequest
from pywps import LiteralInput, ComplexOutput, FORMATS
import sentry_sdk

from finch.processes import make_xclim_indicator_process, SubsetGridPointProcess
from finch.processes.subset import SubsetProcess
from finch.processes.utils import get_bccaqv2_inputs
from finch.processes.wps_xclim_indices import make_nc_input


LOGGER = logging.getLogger("PYWPS")


class BCCAQV2HeatWave(SubsetGridPointProcess):
    """Subset a NetCDF file using a gridpoint, and then compute the 'heat wave' index."""

    def __init__(self):
        self.indices_process = make_xclim_indicator_process(heat_wave_frequency)
        inputs = [
            i
            for i in self.indices_process.inputs
            if i.identifier not in ["tasmin", "tasmax"]
        ]
        inputs += [
            LiteralInput(
                "lon",
                "Longitude of point",
                abstract="Longitude located inside the grid-cell to extract.",
                data_type="float",
            ),
            LiteralInput(
                "lat",
                "Latitude of point",
                abstract="Latitude located inside the grid-cell to extract.",
                data_type="float",
            ),
            LiteralInput(
                "y0",
                "Initial year",
                abstract="Initial year for temporal subsetting. Defaults to first year in file.",
                data_type="integer",
                min_occurs=0,
            ),
            LiteralInput(
                "y1",
                "Final year",
                abstract="Final year for temporal subsetting. Defaults to last year in file.",
                data_type="integer",
                min_occurs=0,
            ),
            LiteralInput(
                "output_format",
                "Output format choice",
                abstract="Choose in which format you want to recieve the result",
                data_type="string",
                allowed_values=["netcdf", "csv"],
                default="netcdf",
                min_occurs=0,
            ),
        ]

        outputs = [
            ComplexOutput(
                "output",
                "Result",
                abstract="The format depends on the input parameter 'output_format'",
                as_reference=True,
                supported_formats=[FORMATS.NETCDF, FORMATS.TEXT],
            )
        ]

        SubsetProcess.__init__(
            self,
            self._handler,
            identifier="BCCAQv2_heat_wave_frequency_gridpoint",
            title="BCCAQv2 grid cell heat wave frequency computation",
            version="0.1",
            abstract=(
                "Compute heat wave frequency for all the "
                "BCCAQv2 datasets for a single grid cell."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _make_tasmin_tasmax_pairs(self, filenames: List[str]):
        tasmin_files = [f for f in filenames if "tasmin" in f.lower()]
        tasmax_files = [f for f in filenames if "tasmax" in f.lower()]
        for tasmin in tasmin_files[:]:
            for tasmax in tasmax_files[:]:
                if tasmin.lower() == tasmax.lower().replace("tasmax", "tasmin"):
                    yield tasmin, tasmax
                    tasmax_files.remove(tasmax)
                    tasmin_files.remove(tasmin)
                    break
        for f in tasmax_files + tasmax_files:
            sentry_sdk.capture_message(
                f"Couldn't find matching tasmin or tasmax for: {f}", level="error"
            )

    def _handler(self, request: WPSRequest, response: ExecuteResponse):
        self.write_log("Processing started", response, 5)

        self.write_log("Fetching BCCAQv2 datasets", response, 6)
        tasmin_inputs = get_bccaqv2_inputs(request.inputs, "tasmin")["resource"]
        tasmax_inputs = get_bccaqv2_inputs(request.inputs, "tasmax")["resource"]

        request.inputs["resource"] = tasmin_inputs + tasmax_inputs

        self.write_log("Running subset", response, 7)

        metalink = self.subset(
            request.inputs, response, start_percentage=7, end_percentage=50
        )

        if not metalink.files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        self.write_log("Subset done, calculating indices", response)

        all_files = [f.file for f in metalink.files]

        start_percentage = 50
        end_percentage = 95

        pairs = list(self._make_tasmin_tasmax_pairs(all_files))
        n_pairs = len(pairs)

        for n, (tasmin, tasmax) in enumerate(pairs):
            percentage = start_percentage + int(
                n / n_pairs * (end_percentage - start_percentage)
            )
            self.write_log(
                f"Processing file {n + 1} of {n_pairs}", response, percentage
            )

            compute_inputs = [i.identifier for i in self.indices_process.inputs]
            inputs = defaultdict(list)
            for i in request.inputs:
                if i.identifier in compute_inputs:
                    inputs[i].append(i)

            tasmin_input = make_nc_input("tasmin")
            tasmin_input.file = tasmin
            inputs["tasmin"] = [tasmin_input]
            tasmax_input = make_nc_input("tasmax")
            tasmax_input.file = tasmax
            inputs["tasmax"] = [tasmax_input]

            self.compute_indices(self.indices_process, inputs)

        self.write_log("Computation done, creating zip file", response)

        lat = request.inputs["lat"]
        lon = request.inputs["lon"]
        filename = f"BCCAQv2_subset_heat_wave_frequency_{lat}_{lon}.zip"
        output_zip = Path(self.workdir) / filename
        self.zip_metalink(output_zip, metalink, response, 95)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["zip"].file = output_zip
        return response
