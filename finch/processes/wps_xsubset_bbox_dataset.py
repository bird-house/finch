from pathlib import Path

from pywps.app import WPSRequest
from pywps.app.exceptions import ProcessError
from pywps.response.execute import ExecuteResponse

from .ensemble_utils import get_datasets, make_output_filename
from .subset import finch_subset_bbox
from .utils import netcdf_file_list_to_csv, single_input_or_none, write_log, zip_files
from .wps_base import FinchProcess
from . import wpsio


class SubsetBboxDatasetProcess(FinchProcess):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            wpsio.variable,
            wpsio.rcp,
            wpsio.lon0,
            wpsio.lon1,
            wpsio.lat0,
            wpsio.lat1,
            wpsio.start_date,
            wpsio.end_date,
            wpsio.output_format_netcdf_csv,
            wpsio.dataset_name,
        ]

        outputs = [wpsio.output_netcdf_csv]

        super().__init__(
            self._handler,
            identifier="subset_bbox_dataset",
            title="Subset of a dataset, using a bounding box",
            version="0.1",
            abstract=(
                "For the given dataset, "
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

        write_log(self, "Fetching datasets")

        variable = request.inputs["variable"][0].data
        variables = None if variable is None else [variable]
        rcp = single_input_or_none(request.inputs, "rcp")

        dataset_name = single_input_or_none(request.inputs, "dataset_name")
        request.inputs["resource"] = get_datasets(
            dataset_name, workdir=self.workdir, variables=variables, rcp=rcp
        )

        write_log(self, "Running subset", process_step="subset")

        output_files = finch_subset_bbox(
            self,
            netcdf_inputs=request.inputs["resource"],
            request_inputs=request.inputs,
        )

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


class SubsetBboxBCCAQV2Process(SubsetBboxDatasetProcess):
    def __init__(self):
        """*** Deprecated *** to be removed in a future release"""
        super().__init__()
        self.identifier = "subset_ensemble_bbox_BCCAQv2"
        self.title = "Subset of BCCAQv2 datasets, using a bounding box"
        self.version = "0.1"
        self.abstract = (
            "For the BCCAQv2 datasets, "
            "return the data for which grid cells intersect the "
            "bounding box for each input dataset as well as "
            "the time range selected."
        )
