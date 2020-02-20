from collections import deque
import logging
from pathlib import Path
import warnings

from pywps import LiteralInput
from pywps.app import WPSRequest
from pywps.app.exceptions import ProcessError
from pywps.response.execute import ExecuteResponse
from xclim.atmos import heat_wave_frequency

from .ensemble_utils import fix_broken_time_indices, get_datasets, make_output_filename
from .subset import finch_subset_gridpoint
from .utils import (
    compute_indices,
    make_tasmin_tasmax_pairs,
    netcdf_file_list_to_csv,
    single_input_or_none,
    write_log,
    zip_files,
)
from .wps_base import FinchProcess, make_xclim_indicator_process
from .wps_xclim_indices import XclimIndicatorBase, make_nc_input
from . import wpsio

LOGGER = logging.getLogger("PYWPS")


class BCCAQV2HeatWave(FinchProcess):
    """Subset a NetCDF file using a gridpoint, and then compute the 'heat wave' index.

    *** Deprecated *** to be removed in a future release
    """

    def __init__(self):
        self.indices_process = make_xclim_indicator_process(
            heat_wave_frequency,
            class_name_suffix="BCCAQV2HeatWave",
            base_class=XclimIndicatorBase,
        )
        inputs = [
            i
            for i in self.indices_process.inputs
            if i.identifier not in ["tasmin", "tasmax"]
        ]
        inputs += [
            wpsio.lon,
            wpsio.lat,
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
            wpsio.output_format_netcdf_csv,
        ]

        outputs = [wpsio.output_netcdf_zip]

        super().__init__(
            self._handler,
            identifier="BCCAQv2_heat_wave_frequency_gridpoint",
            title=(
                "BCCAQv2 grid cell heat wave frequency computation"
                "*** Deprecated *** to be removed in a future release"
            ),
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

        self.status_percentage_steps = {
            "start": 5,
            "subset": 7,
            "compute_indices": 70,
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

        rcp = single_input_or_none(request.inputs, "rcp")

        request.inputs["resource"] = get_datasets(
            "bccaqv2", workdir=self.workdir, variables=["tasmin", "tasmax"], rcp=rcp
        )

        write_log(self, "Running subset", process_step="subset")

        output_files = finch_subset_gridpoint(
            self,
            netcdf_inputs=request.inputs["resource"],
            request_inputs=request.inputs,
        )

        if not output_files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        write_log(
            self, "Subset done, calculating indices", process_step="compute_indices"
        )

        pairs = list(make_tasmin_tasmax_pairs(output_files))
        n_pairs = len(pairs)

        output_files = []

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        for n, (tasmin, tasmax) in enumerate(pairs):
            write_log(
                self,
                f"Computing indices for file {n + 1} of {n_pairs}",
                subtask_percentage=n * 100 // n_pairs,
            )

            tasmin, tasmax = fix_broken_time_indices(tasmin, tasmax)

            compute_inputs = [i.identifier for i in self.indices_process.inputs]
            inputs = {k: v for k, v in request.inputs.items() if k in compute_inputs}

            inputs["tasmin"] = deque([make_nc_input("tasmin")], maxlen=1)
            inputs["tasmin"][0].file = str(tasmin)
            inputs["tasmax"] = deque([make_nc_input("tasmax")], maxlen=1)
            inputs["tasmax"][0].file = str(tasmax)

            out = compute_indices(self, self.indices_process.xci, inputs)
            out_fn = Path(self.workdir) / tasmin.name.replace(
                "tasmin", "heat_wave_frequency"
            )
            out.to_netcdf(out_fn)
            output_files.append(out_fn)

        warnings.filterwarnings("default", category=FutureWarning)
        warnings.filterwarnings("default", category=UserWarning)

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
