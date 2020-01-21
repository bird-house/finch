from collections import deque
import logging
from pathlib import Path
import warnings

from pywps import ComplexOutput, FORMATS, LiteralInput
from pywps.app import WPSRequest
from pywps.app.exceptions import ProcessError
from pywps.response.execute import ExecuteResponse
from xclim.atmos import heat_wave_frequency

from finch.processes import make_xclim_indicator_process

from .base import FinchProcess
from .bccaqv2 import get_bccaqv2_inputs, make_output_filename, fix_broken_time_indices
from .subset import finch_subset_gridpoint
from .utils import (
    compute_indices,
    make_tasmin_tasmax_pairs,
    netcdf_to_csv,
    single_input_or_none,
    write_log,
    zip_files,
)
from .wps_xclim_indices import make_nc_input
from .wpsio import lat, lon

LOGGER = logging.getLogger("PYWPS")


class BCCAQV2HeatWave(FinchProcess):
    """Subset a NetCDF file using a gridpoint, and then compute the 'heat wave' index."""

    def __init__(self):
        self.indices_process = make_xclim_indicator_process(heat_wave_frequency)
        inputs = [
            i
            for i in self.indices_process.inputs
            if i.identifier not in ["tasmin", "tasmax"]
        ]
        inputs += [
            lon,
            lat,
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

        super().__init__(
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
        self.percentage = 5
        write_log(self, "Processing started")

        output_filename = make_output_filename(self, request.inputs)

        write_log(self, "Fetching BCCAQv2 datasets")

        variable = single_input_or_none(request.inputs, "variable")
        rcp = single_input_or_none(request.inputs, "rcp")
        request.inputs = get_bccaqv2_inputs(request.inputs, variable=variable, rcp=rcp)

        self.percentage = 7
        write_log(self, "Running subset")

        output_files = finch_subset_gridpoint(self, request.inputs)

        if not output_files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        write_log(self, "Subset done, calculating indices")

        pairs = list(make_tasmin_tasmax_pairs(output_files))
        n_pairs = len(pairs)

        output_files = []

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        for n, (tasmin, tasmax) in enumerate(pairs):
            percentage = int(n / n_pairs * 100)
            write_log(self, f"Computing indices for file {n + 1} of {n_pairs}")

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

        if request.inputs["output_format"][0].data == "csv":
            csv_files, metadata_folder = netcdf_to_csv(
                output_files,
                output_folder=Path(self.workdir),
                filename_prefix=output_filename,
            )
            output_files = csv_files + [metadata_folder]

        output_zip = Path(self.workdir) / (output_filename + ".zip")

        def _log(message_, percentage_):
            write_log(self, message_)

        zip_files(output_zip, output_files, log_function=_log)

        response.outputs["output"].file = output_zip

        write_log(self, "Processing finished successfully")
        return response
