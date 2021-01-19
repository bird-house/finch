import logging
from typing import Dict, List

from dask.diagnostics import ProgressBar
from pywps import ComplexInput, FORMATS, LiteralInput, Process
from pywps.app.Common import Metadata
from sentry_sdk import configure_scope
import xclim

from finch.processes.utils import PywpsInput


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
    def __init__(
        self, logging_function, start_percentage=0, end_percentage=100, *args, **kwargs
    ):
        super(FinchProgressBar, self).__init__(*args, **kwargs)
        self.start = start_percentage
        self.end = end_percentage
        self._logging_function = logging_function

    def _draw_bar(self, frac, elapsed):
        real_frac = (self.start + frac * (self.end - self.start)) / 100
        bar = "#" * int(self._width * real_frac)
        percent = int(100 * real_frac)
        msg = "[{0:<{1}}] | {2}% Done".format(bar, self._width, percent)

        self._logging_function(msg, real_frac * 100)


def make_xclim_indicator_process(
    xci, class_name_suffix: str, base_class
) -> FinchProcess:
    """Create a WPS Process subclass from an xclim `Indicator` class instance.

    Adds translations for title and abstract properties of the process and its inputs and outputs.

    Parameters
    ----------
    xci : Indicator
      Indicator instance.
    class_name_suffix : str
      Suffix appended to the indicator identifier to create the Process subclass name.
    base_class : cls
      Class that will be subclassed to create indicator Process.
    """
    attrs = xci.json()

    # Sanitize name
    name = attrs["identifier"].replace("{", "_").replace("}", "_").replace("__", "_")

    process_class = type(
        str(name) + class_name_suffix,
        (base_class,),
        {"xci": xci, "__doc__": attrs["abstract"]},
    )

    process = process_class()
    process.translations = {  # type: ignore
        locale: xclim.core.locales.get_local_attrs(xci.identifier.upper(), locale, append_locale_name=False)
        for locale in xclim.core.locales.list_locales()
    }

    return process  # type: ignore


NC_INPUT_VARIABLES = [
    "tas",
    "tasmin",
    "tasmax",
    "pr",
    "prsn",
    "tn10",
    "tn90",
    "t10",
    "t90",
    "q",
    "da",
    "sic",
    "snd",
    "area",
    "uas",
    "vas",
    "ps",
    "rh",
    "huss",
    "ws",
    "sfcWind",
    "sfcWindfromdir",
]


def convert_xclim_inputs_to_pywps(params: Dict, parent=None) -> List[PywpsInput]:
    """Convert xclim indicators properties to pywps inputs."""
    # Ideally this would be based on the Parameters docstring section rather than name conventions.
    inputs = []

    for name, attrs in params.items():
        if name in NC_INPUT_VARIABLES:
            inputs.append(make_nc_input(name))
        elif name in ["thresh_tasmin", "thresh_tasmax", "sum_thresh"]:
            inputs.append(make_thresh(name, attrs["default"], attrs["description"]))
        elif name in ["thresh", "ice_thresh", "calm_wind_thresh"]:
            inputs.append(make_thresh(name, attrs["default"], attrs["description"]))
        elif name in ["freq"]:
            inputs.append(make_freq(name, attrs["default"], attrs["description"]))
        elif name in ["indexer"]:
            inputs.append(make_month())
            inputs.append(make_season())
        elif name in ["window"]:
            inputs.append(make_window(name, attrs["default"], attrs["description"]))
        elif name in ["mid_date", "before_date", "start_date", "after_date"]:
            inputs.append(make_date_of_year(name, attrs["default"], attrs["description"]))
        elif name in ["op"]:
            if "reduce" in attrs["description"].lower():
                inputs.append(make_reduce_op(name, attrs["default"], attrs["description"]))
            else:
                inputs.append(make_binary_op(name, attrs["default"], attrs["description"]))
        elif name in ["mode"]:
            inputs.append(make_mode(name, attrs["default"], attrs["description"]))
        elif name in ["start_date", "end_date"]:
            inputs.append(make_datetime(name, attrs["default"], attrs["description"]))
        elif name in ["t"]:
            inputs.append(make_return_period(name, attrs["default"], attrs["description"]))
        elif name in ["dist"]:
            inputs.append(make_distribution(name, attrs["default"], attrs["description"]))
        elif name in ["method"]:
            inputs.append(make_fit_method(name, attrs["default"], attrs["description"]))
        else:
            # raise NotImplementedError(f"{parent}: {name}")
            LOGGER.warning(f"{parent}: {name} is not implemented.")

    return inputs


def make_freq(name, default="YS", abstract="", allowed=("YS", "MS", "QS-DEC", "AS-JUL")):
    return LiteralInput(
        name,
        "Frequency",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
        allowed_values=allowed,
    )


def make_thresh(name, default, abstract=""):
    return LiteralInput(
        identifier=name,
        title="Threshold",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
    )


def make_window(name, default, abstract=""):
    return LiteralInput(
        name,
        "Window",
        abstract=abstract,
        data_type="integer",
        min_occurs=0,
        max_occurs=1,
        default=default,
    )


def make_mode(name, default="max", abstract=""):
    if default == "none":
        default = "max"
    return LiteralInput(
        name,
        "Mode",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
        allowed_values=["min", "max"]
    )


def make_date_of_year(name, default, abstract=""):
    return LiteralInput(
        name,
        "Date of the year",
        abstract=abstract,
        data_type="string",
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
        max_occurs=10000,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    )


def make_binary_op(name, default=">", abstract=""):
    return LiteralInput(
        identifier=name,
        title="Binary operation",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
        allowed_values=[">", "<", ">=", "<=", "gt", "lt", "ge", "le"]
    )


def make_reduce_op(name, default="max", abstract=""):
    if default == "none":
        default = "max"
    return LiteralInput(
        identifier=name,
        title="Reduce operation",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
        allowed_values=['min', 'max', 'mean', 'std', 'var', 'count', 'sum', 'argmax', 'argmin']
    )


def make_datetime(name, default, abstract=""):
    return LiteralInput(
        identifier=name,
        title="Datetime",
        abstract=abstract,
        data_type="datetime",
        min_occurs=0,
        max_occurs=1,
        default=default,
    )


def make_return_period(name, default, abstract=""):
    return LiteralInput(
        identifier=name,
        title="Datetime",
        abstract=abstract,
        data_type="integer",
        min_occurs=1,
        max_occurs=100,
    )


def make_distribution(name, default, abstract=""):
    return LiteralInput(
        identifier=name,
        title="Statistical distribution",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
    )


def make_fit_method(name, default, abstract=""):
    return LiteralInput(
        identifier=name,
        title="Parameter fitting method",
        abstract=abstract,
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        default=default,
        allowed_values=["ML", "PWM"]
    )


def make_month():
    return LiteralInput(
        identifier="month",
        title="Select by month",
        abstract="Months of the year over which to compute indicator.",
        data_type="integer",
        min_occurs=0,
        max_occurs=12,
        allowed_values=list(range(1, 13))
    )


def make_season():
    return LiteralInput(
        identifier="season",
        title="Select by season",
        abstract="Climatological season over which to compute indicator.",
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        allowed_values=["DJF", "MAM", "JJA", "SON"]
    )
