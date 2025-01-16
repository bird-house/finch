# noqa: D100
from pathlib import Path

from pywps import LiteralInput
from pywps.app import WPSRequest
from pywps.app.exceptions import ProcessError
from pywps.response.execute import ExecuteResponse

from . import wpsio
from .ensemble_utils import get_datasets, make_output_filename
from .subset import finch_subset_gridpoint
from .utils import (
    get_datasets_config,
    netcdf_file_list_to_csv,
    single_input_or_none,
    write_log,
    zip_files,
)
from .wps_base import FinchProcess


class SubsetGridPointDatasetProcess(FinchProcess):
    """Subset a NetCDF file grid cells using a list of coordinates."""

    def __init__(self):
        inputs = [
            *wpsio.get_ensemble_inputs(),
            wpsio.copy_io(wpsio.lat, min_occurs=0),
            wpsio.copy_io(wpsio.lon, min_occurs=0),
            LiteralInput(
                "lat0",
                "Latitude (deprecated, use 'lat')",
                abstract="Latitude (deprecated, use 'lat').",
                data_type="string",
                min_occurs=0,
            ),
            LiteralInput(
                "lon0",
                "Longitude (deprecated, use 'lon')",
                abstract="Latitude (deprecated, use 'lon').",
                data_type="string",
                min_occurs=0,
            ),
            wpsio.start_date,
            wpsio.end_date,
            wpsio.output_format_netcdf_csv,
            wpsio.csv_precision,
        ]

        outputs = [wpsio.output_netcdf_csv]

        super().__init__(
            self._handler,
            identifier="subset_grid_point_dataset",
            title="Subset of grid cells from a dataset, using a list of coordinates",
            version="0.1",
            abstract=(
                "For the the given dataset, "
                "return the closest grid cell for each provided coordinates pair, "
                "for the time range selected."
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

        # Temporary backward-compatibility adjustment.
        # Remove me when lon0 and lat0 are removed
        lon, lat, lon0, lat0 = (
            single_input_or_none(request.inputs, var)
            for var in "lon lat lon0 lat0".split()
        )
        if not (lon and lat or lon0 and lat0):
            raise ProcessError("Provide both lat and lon or both lon0 and lat0.")
        request.inputs.setdefault("lon", request.inputs.get("lon0"))
        request.inputs.setdefault("lat", request.inputs.get("lat0"))
        # End of 'remove me'

        write_log(self, "Fetching datasets")

        variables = [v.data for v in request.inputs.get("variable", [])] or None
        scenario = single_input_or_none(request.inputs, "scenario")
        models = [m.data.strip() for m in request.inputs["models"]]

        dataset_name = single_input_or_none(request.inputs, "dataset")
        dataset = get_datasets_config()[dataset_name]
        request.inputs["resource"] = get_datasets(
            dataset,
            workdir=self.workdir,
            variables=variables,
            scenario=scenario,
            models=models,
        )

        output_filename = Path(make_output_filename(self, request.inputs))

        write_log(self, "Running subset", process_step="subset")

        output_files = finch_subset_gridpoint(
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
                csv_precision=single_input_or_none(request.inputs, "csv_precision"),
            )
            output_files = csv_files + [metadata_folder]

        write_log(self, "Zipping outputs", process_step="zip_outputs")

        output_zip = Path(self.workdir) / output_filename.with_suffix(".zip")

        def _log(message, percentage):
            write_log(self, message, subtask_percentage=percentage)

        zip_files(output_zip, output_files, log_function=_log)

        response.outputs["output"].file = output_zip

        write_log(self, "Processing finished successfully", process_step="done")
        return response
