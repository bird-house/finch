from pathlib import Path

from pywps import LiteralInput, ComplexOutput, FORMATS
from pywps.app import WPSRequest
from pywps.app.exceptions import ProcessError
from pywps.response.execute import ExecuteResponse

from .wps_base import FinchProcess
from .ensemble_utils import get_bccaqv2_inputs, make_output_filename
from .subset import finch_subset_bbox
from .utils import netcdf_file_list_to_csv, single_input_or_none, write_log, zip_files
from .wpsio import end_date, lat0, lat1, lon0, lon1, start_date


class SubsetBboxBCCAQV2Process(FinchProcess):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            LiteralInput(
                "variable",
                "NetCDF Variable",
                abstract=(
                    "Name of the variable in the NetCDF file."
                    "If not provided, all variables will be subsetted."
                ),
                data_type="string",
                default=None,
                min_occurs=0,
                allowed_values=["tasmin", "tasmax", "pr"],
            ),
            LiteralInput(
                "rcp",
                "RCP Scenario",
                abstract="Representative Concentration Pathway (RCP)",
                data_type="string",
                default=None,
                min_occurs=0,
                allowed_values=["rcp26", "rcp45", "rcp85"],
            ),
            lon0,
            lon1,
            lat0,
            lat1,
            start_date,
            end_date,
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

        super().__init__(
            self._handler,
            identifier="subset_ensemble_bbox_BCCAQv2",
            title="Subset of BCCAQv2 datasets, using a bounding box",
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

        self.status_percentage_steps = {
            "start": 5,
            "subset": 7,
            "convert_to_csv": 90,
            "zip_outputs": 95,
            "done": 99,
        }

    def _handler(self, request: WPSRequest, response: ExecuteResponse):

        convert_to_csv = request.inputs["output_format"][0].data == "csv"
        if not convert_to_csv:
            del self.status_percentage_steps["convert_to_csv"]

        write_log(self, "Processing started", process_step="start")

        output_filename = make_output_filename(self, request.inputs)

        write_log(self, "Fetching BCCAQv2 datasets")

        variable = single_input_or_none(request.inputs, "variable")
        rcp = single_input_or_none(request.inputs, "rcp")
        request.inputs["resource"] = get_bccaqv2_inputs(
            request.inputs, variable=variable, rcp=rcp
        )

        write_log(self, "Running subset", process_step="subset")

        output_files = finch_subset_bbox(self, request.inputs)

        if not output_files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        if convert_to_csv:
            write_log(self, "Converting outputs to csv", process_step="convert_to_csv")

            csv_files, metadata_folder = netcdf_file_list_to_csv(
                output_files,
                output_folder=Path(self.workdir),
                filename_prefix=output_filename,
            )
            output_files = csv_files + [metadata_folder]

        write_log(self, "Zipping outputs", process_step="zip_outputs")

        output_zip = Path(self.workdir) / (output_filename + ".zip")

        def _log(message, percentage):
            write_log(self, message, subtask_percentage=percentage)

        zip_files(output_zip, output_files, log_function=_log)

        response.outputs["output"].file = output_zip

        write_log(self, "Processing finished successfully", process_step="done")
        return response
