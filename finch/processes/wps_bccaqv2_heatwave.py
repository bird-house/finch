from xclim.atmos import heat_wave_frequency
from pathlib import Path
from pywps.response.execute import ExecuteResponse
from pywps.app.exceptions import ProcessError
from pywps.app import WPSRequest
from pywps import LiteralInput, ComplexOutput, FORMATS

from finch.processes import make_xclim_indicator_process, SubsetGridPointProcess
from finch.processes.subset import SubsetProcess
from finch.processes.utils import get_bccaqv2_inputs


class BCCAQV2HeatWave(SubsetGridPointProcess):
    """Subset a NetCDF file using a gridpoint, and then compute the 'heat wave' index."""

    def __init__(self):
        heat_wave_process = make_xclim_indicator_process(heat_wave_frequency)
        inputs = [i for i in heat_wave_process.inputs if i.identifier not in ["tasmin", "tasmax"]]
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

    def _handler(self, request: WPSRequest, response: ExecuteResponse):
        self.write_log("Processing started", response, 5)

        variable = request.inputs["variable"][0].data
        rcp = request.inputs["rcp"][0].data

        self.write_log("Fetching BCCAQv2 datasets", response, 6)
        request.inputs = get_bccaqv2_inputs(request.inputs, variable, rcp)

        self.write_log("Running subset", response, 7)

        metalink = self.subset(request.inputs, response, start_percentage=7, end_percentage=90)

        if not metalink.files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        self.write_log("Subset done, crating zip file", response)

        output_zip = Path(self.workdir) / f"BCCAQv2_subset_{rcp}_{variable}.zip"
        self.zip_metalink(output_zip, metalink, response, 90)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["zip"].file = output_zip
        return response
