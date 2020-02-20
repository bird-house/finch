import logging
import os

from pywps import ComplexInput, ComplexOutput, FORMATS, LiteralInput
from pywps.app.Common import Metadata
from unidecode import unidecode

from finch.processes.utils import dataset_to_netcdf, drs_filename
from finch.processes.wps_base import convert_xclim_inputs_to_pywps

from .utils import compute_indices, log_file_path, write_log
from .wps_base import FinchProcess, FinchProgressBar
from pathlib import Path

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
            ComplexOutput(
                "output_log",
                "Logging information",
                abstract="Collected logs during process run.",
                as_reference=True,
                supported_formats=[FORMATS.TEXT],
            ),
        ]

        super().__init__(
            self._handler,
            identifier=attrs["identifier"],
            version="0.1",
            title=unidecode(attrs["long_name"]),
            abstract=unidecode(attrs["abstract"]),
            inputs=convert_xclim_inputs_to_pywps(eval(attrs["parameters"])),
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {
            "start": 5,
            "done": 99,
        }

    def load_inputs(self, params):
        # Ideally this would be based on the Parameters docstring section rather than name conventions.
        inputs = []

        for name, attrs in params.items():
            if name in ["tas", "tasmin", "tasmax", "pr", "prsn"]:
                inputs.append(make_nc_input(name))
            elif name in ["tn10", "tn90", "t10", "t90"]:
                inputs.append(make_nc_input(name))
            elif name in ["thresh_tasmin", "thresh_tasmax"]:
                inputs.append(make_thresh(name, attrs["default"], attrs["desc"]))
            elif name in ["thresh"]:
                inputs.append(make_thresh(name, attrs["default"], attrs["desc"]))
            elif name in ["freq"]:
                inputs.append(make_freq(name, attrs["default"]))
            elif name in ["window"]:
                inputs.append(make_window(name, attrs["default"], attrs["desc"]))
            else:
                # raise NotImplementedError(name)
                LOGGER.warning("not implemented: {}".format(name))

        return inputs

    def _handler(self, request, response):
        write_log(self, "Computing the output netcdf", process_step="start")

        out = compute_indices(self, self.xci, request.inputs)
        try:
            filename = drs_filename(out)
        except KeyError:
            filename = "out.nc"
        out_fn = Path(self.workdir, filename)

        def _log(message, percentage):
            write_log(self, message, subtask_percentage=percentage)

        with FinchProgressBar(
            logging_function=_log,
            start_percentage=self.response.status_percentage,
            width=15,
            dt=1,
        ):
            dataset_to_netcdf(out, out_fn)

        response.outputs["output_netcdf"].file = out_fn
        response.outputs["output_log"].file = log_file_path(self)

        write_log(self, "Processing finished successfully", process_step="done")

        return response


def make_freq(name, default="YS", allowed=("YS", "MS", "QS-DEC", "AS-JUL")):
    return LiteralInput(
        name,
        "Frequency",
        abstract="Resampling frequency",
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
        allowed_values=allowed,
    )


def make_thresh(name, default, abstract=""):
    return LiteralInput(
        name,
        "threshold",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
    )


def make_window(name, default, abstract=""):
    return LiteralInput(
        name,
        "window",
        abstract=abstract,
        data_type="integer",
        min_occurs=0,
        max_occurs=1,
        default=default,
    )


def make_nc_input(name):
    return ComplexInput(
        name,
        "Resource",
        abstract="NetCDF Files or archive (tar/zip) containing netCDF files.",
        metadata=[Metadata("Info")],
        min_occurs=1,
        max_occurs=1,
        supported_formats=[FORMATS.NETCDF],
    )
