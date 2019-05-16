from pathlib import Path
from pywps.response.execute import ExecuteResponse
from pywps.app.exceptions import ProcessError
from pywps.app import WPSRequest
from pywps import LiteralInput, ComplexOutput, FORMATS

from finch.processes import SubsetBboxProcess
from finch.processes.subset import SubsetProcess
from finch.processes.utils import get_bccaqv2_inputs


class SubsetBCCAQV2Process(SubsetBboxProcess):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            LiteralInput(
                "rcp",
                "RCP Scenario",
                abstract="Representative Concentration Pathway (RCP)",
                data_type="string",
                allowed_values=["rcp26", "rcp45", "rcp85"],
            ),
            LiteralInput(
                "variable",
                "NetCDF Variable",
                abstract="Name of the variable in the NetCDF file.",
                data_type="string",
                allowed_values=["tasmin", "tasmax", "pr"],
            ),
            LiteralInput(
                "lon0",
                "Minimum longitude",
                abstract="Minimum longitude.",
                data_type="float",
                default=-180,
                min_occurs=0,
            ),
            LiteralInput(
                "lon1",
                "Maximum longitude",
                abstract="Maximum longitude.",
                data_type="float",
                default=180,
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
            ),
            LiteralInput(
                "y1",
                "Final year",
                abstract="Final year for temporal subsetting. Defaults to last year in file.",
                data_type="integer",
                default=None,
                min_occurs=0,
            ),
        ]

        outputs = [
            ComplexOutput(
                "zip",
                "Zip file",
                abstract="A zip file containing all the output files.",
                as_reference=True,
                supported_formats=[FORMATS.ZIP],
            )
        ]

        SubsetProcess.__init__(
            self,
            self._handler,
            identifier="subset_ensemble_BCCAQv2",
            title="Subset of BCCAQv2 datasets",
            version="0.1",
            abstract=(
                "For the BCCAQv2 datasets, "
                "return the data for which grid cells intersect the "
                "bounding box for each input dataset as well as "
                "the time range selected."
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

        self.write_log("Subset done, creating zip file", response)

        output_zip = Path(self.workdir) / f"BCCAQv2_subset_{rcp}_{variable}.zip"
        self.zip_metalink(output_zip, metalink, response, 90)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["zip"].file = output_zip
        return response
