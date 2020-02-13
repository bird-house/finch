from finch.processes.utils import PywpsInput
import logging
from typing import Dict, List

from dask.diagnostics import ProgressBar
from dask.diagnostics.progress import format_time
from pywps import ComplexInput, FORMATS, LiteralInput, Process
from pywps.app.Common import Metadata
from sentry_sdk import configure_scope


LOGGER = logging.getLogger("PYWPS")


class FinchProcess(Process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Must be assigned to the instance so that
        # it's also copied over when the process is deepcopied
        self.wrapped_handler = self.handler
        self.handler = self._handler_wrapper
        self.response = None
        # A dict containing a step description and the percentage at the strat of this step
        # Each process should overwrite this, and thie values are used in `processes.utils.write_log`
        self.status_percentage_steps: Dict[str, int] = {}

    def _handler_wrapper(self, request, response):
        self.sentry_configure_scope(request)

        # The process has been deepcopied, so it's ok to assign it a single response.
        # We can now update the status document from the process instance itself.
        self.response = response
        return self.wrapped_handler(request, response)

    def sentry_configure_scope(self, request):
        """Add additional data to sentry error messages.

        When sentry is not initialized, this won't add any overhead.
        """
        with configure_scope() as scope:
            scope.set_extra("identifier", self.identifier)
            scope.set_extra("request_uuid", str(self.uuid))
            if request.http_request:
                # if the request has been put in the `stored_requests` table by pywps
                # the original request.http_request is not available anymore
                scope.set_extra("host", request.http_request.host)
                scope.set_extra("remote_addr", request.http_request.remote_addr)
                scope.set_extra("xml_request", request.http_request.data)


class FinchProgressBar(ProgressBar):
    def __init__(self, logging_function, start_percentage, *args, **kwargs):
        super(FinchProgressBar, self).__init__(*args, **kwargs)
        self._logging_function = logging_function

    def _draw_bar(self, frac, elapsed):
        bar = "#" * int(self._width * frac)
        percent = int(100 * frac)
        elapsed = format_time(elapsed)
        msg = "[{0:<{1}}] | {2}% Done | {3}".format(bar, self._width, percent, elapsed)

        self._logging_function(msg, percent)


def make_xclim_indicator_process(
    xci, class_name_suffix: str, base_class
) -> FinchProcess:
    """Create a WPS Process subclass from an xclim `Indicator` class instance."""
    attrs = xci.json()

    # Sanitize name
    name = attrs["identifier"].replace("{", "_").replace("}", "_").replace("__", "_")

    process_class = type(
        str(name) + class_name_suffix,
        (base_class,),
        {"xci": xci, "__doc__": attrs["abstract"]},
    )

    return process_class()  # type: ignore


def convert_xclim_inputs_to_pywps(params: Dict) -> List[PywpsInput]:
    """Convert xclim indicators properties to pywps inputs."""
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