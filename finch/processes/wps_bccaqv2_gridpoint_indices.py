from copy import deepcopy
import logging
import os
from pathlib import Path
import warnings

from pywps import ComplexInput, ComplexOutput, FORMATS, LiteralInput
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from unidecode import unidecode

from finch.processes.subset import finch_subset_gridpoint
from finch.processes.utils import netcdf_to_csv, zip_files
from finch.processes.utils_bccaqv2 import make_indicator_inputs

from . import wpsio
from .base import convert_xclim_inputs_to_pywps
from .base import FinchProcess, FinchProgressBar
from .utils import compute_indices, log_file_path, single_input_or_none, write_log
from .utils_bccaqv2 import (
    bccaq_variable_types,
    get_bccaqv2_inputs,
    make_output_filename,
    xclim_netcdf_variables,
)

LOGGER = logging.getLogger("PYWPS")


class XclimEnsembleGridPointBase(FinchProcess):
    """Dummy xclim indicator process class.

    Set xci to the xclim indicator in order to have a working class"""

    xci = None

    def __init__(self):
        """Create a WPS process from an xclim indicator class instance."""

        if self.xci is None:
            raise AttributeError(
                "Use the `finch.processes.base.make_xclim_indicator_process` function instead."
            )

        attrs = self.xci.json()

        outputs = [
            ComplexOutput(
                "output",
                "Result",
                abstract=(
                    f"{attrs['standard_name']}."
                    "The format depends on the input parameter 'output_format'."
                ),
                as_reference=True,
                supported_formats=[
                    FORMATS.NETCDF,
                    FORMATS.TEXT,  # Todo: FORMATS.CSV is missing. Is this required to be csv?
                ],
            ),
            ComplexOutput(
                "output_log",
                "Logging information",
                abstract="Collected logs during process run.",
                as_reference=True,
                supported_formats=[FORMATS.TEXT],
            ),
        ]
        inputs = [wpsio.lat, wpsio.lon, wpsio.start_date, wpsio.end_date]

        rcp = deepcopy(wpsio.rcp)
        rcp.min_occurs = 1
        inputs.append(rcp)

        for i in convert_xclim_inputs_to_pywps(eval(attrs["parameters"])):
            if i not in xclim_netcdf_variables:
                inputs.append(i)

        inputs.append(wpsio.output_netcdf_csv)

        super().__init__(
            self._handler,
            identifier=attrs["identifier"],
            version="0.1",
            title=unidecode(attrs["long_name"]),
            abstract=unidecode(attrs["abstract"]),
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

    def _handler(self, request, response):
        convert_to_csv = request.inputs["output_format"][0].data == "csv"
        if not convert_to_csv:
            del self.status_percentage_steps["convert_to_csv"]

        write_log(self, "Processing started", process_step="start")

        output_filename = make_output_filename(self, request.inputs)

        write_log(self, "Fetching BCCAQv2 datasets")

        rcp = single_input_or_none(request.inputs, "rcp")
        request.inputs = get_bccaqv2_inputs(request.inputs, rcp=rcp)

        write_log(self, "Running subset", process_step="subset")

        output_files = finch_subset_gridpoint(self, request.inputs)

        if not output_files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        write_log(self, "Computing indices", process_step="compute_indices")

        input_groups = make_indicator_inputs(self.xci, request.inputs, output_files)
        n_groups = len(input_groups)

        output_files = []

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        for n, inputs in enumerate(input_groups):
            write_log(
                self,
                f"Computing indices for file {n + 1} of {n_groups}",
                subtask_percentage=n * 100 // n_groups,
            )
            output_ds = compute_indices(self, self.xci, inputs)

            output_name = f"{output_filename}_{self.identifier}_{n}.nc"
            for variable in bccaq_variable_types:
                if variable in inputs:
                    input_name = Path(inputs.get(variable)[0].file).name
                    output_name = input_name.replace(variable, self.identifier)

            output_path = Path(self.workdir) / output_name
            output_ds.to_netcdf(output_path)
            output_files.append(output_path)

        warnings.filterwarnings("default", category=FutureWarning)
        warnings.filterwarnings("default", category=UserWarning)

        if convert_to_csv:
            write_log(self, "Converting outputs to csv", process_step="convert_to_csv")

            csv_files, metadata_folder = netcdf_to_csv(
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
