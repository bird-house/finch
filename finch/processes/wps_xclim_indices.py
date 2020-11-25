from collections import deque
import logging
from pathlib import Path
from typing import List

from pywps import ComplexOutput, FORMATS
from pywps.app.exceptions import ProcessError
from unidecode import unidecode
import xarray as xr

from . import wpsio
from .utils import (
    compute_indices,
    dataset_to_netcdf,
    drs_filename,
    log_file_path,
    make_metalink_output,
    write_log,
)
from .wps_base import (
    FinchProcess,
    FinchProgressBar,
    NC_INPUT_VARIABLES,
    convert_xclim_inputs_to_pywps,
)

LOGGER = logging.getLogger("PYWPS")


class XclimIndicatorBase(FinchProcess):
    """Dummy xclim indicator process class.

    Set xci to the xclim indicator in order to have a working class"""

    xci = None

    def __init__(self):
        """Create a WPS process from an xclim indicator class instance."""

        if self.xci is None:
            raise AttributeError(
                "Use the `make_xclim_indicator_process` function instead."
            )

        attrs = self.xci.json()

        outputs = [
            ComplexOutput(
                "output_netcdf",
                "Function output in netCDF",
                abstract="The indicator values computed on the original input grid.",
                as_reference=True,
                supported_formats=[
                    FORMATS.NETCDF,
                ],  # To support FORMATS.DODS we need to get the URL.
            ),
            wpsio.output_log,
            wpsio.output_metalink,
        ]

        super().__init__(
            self._handler,
            identifier=attrs["identifier"],
            version="0.1",
            title=unidecode(attrs["title"]),
            abstract=unidecode(attrs["abstract"]),
            inputs=convert_xclim_inputs_to_pywps(attrs["parameters"], attrs["identifier"]),
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {
            "start": 5,
            "done": 99,
        }

    def _handler(self, request, response):
        write_log(self, "Computing the output netcdf", process_step="start")

        nc_inputs, other_inputs = {}, {}
        for k, v in request.inputs.items():
            if k in NC_INPUT_VARIABLES:
                nc_inputs[k] = v
            else:
                other_inputs[k] = v

        n_files = len(list(nc_inputs.values())[0])

        if not all(n_files == len(v) for v in nc_inputs.values()):
            raise ProcessError(
                f"The count of all netcdf input variables must be equal: {', '.join(nc_inputs)}."
            )

        def _log(message, percentage):
            write_log(self, message, subtask_percentage=percentage)

        output_files = []

        for n in range(n_files):
            # create a dict containting a single netcdf input for each type
            netcdf_inputs = {k: deque([queue[n]]) for k, queue in nc_inputs.items()}
            inputs = {**other_inputs, **netcdf_inputs}

            out = compute_indices(self, self.xci, inputs)
            filename = _make_unique_drs_filename(out, [f.name for f in output_files])
            output_filename = Path(self.workdir, filename)
            output_files.append(output_filename)

            start_percentage = int(n / n_files * 100)
            end_percentage = int((n + 1) / n_files * 100)
            write_log(
                self,
                f"Processing file {n} of {n_files}",
                subtask_percentage=start_percentage,
            )

            with FinchProgressBar(
                logging_function=_log,
                start_percentage=start_percentage,
                end_percentage=end_percentage,
                width=15,
                dt=1,
            ):
                dataset_to_netcdf(out, output_filename)

        metalink = make_metalink_output(self, output_files)

        response.outputs["output_netcdf"].file = str(output_files[0])
        response.outputs["output_log"].file = str(log_file_path(self))
        response.outputs["ref"].data = metalink.xml

        write_log(self, "Processing finished successfully", process_step="done")

        return response


def _make_unique_drs_filename(
    ds: xr.Dataset, existing_names: List[str],
):
    """Generate a drs filename: avoid overwriting files by adding a dash and a number to the filename."""
    try:
        filename = drs_filename(ds)
    except KeyError:
        filename = "out.nc"

    count = 0
    new_filename = filename
    while new_filename in existing_names:
        count += 1
        new_filename = f"{filename.replace('.nc', '')}-{count}.nc"
    return new_filename
