# noqa: D100
import io
import logging
from inspect import _empty as empty_default  # noqa
from typing import Dict, List

import xclim
from dask.diagnostics import ProgressBar
from pywps import FORMATS, ComplexInput, LiteralInput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from sentry_sdk import configure_scope
from xclim.core.utils import InputKind

from .utils import PywpsInput

LOGGER = logging.getLogger("PYWPS")


default_percentiles = {
    "days_over_precip_thresh": {"pr_per": 95},
    "days_over_precip_doy_thresh": {"pr_per": 95},
    "fraction_over_precip_doy_thresh": {"pr_per": 95},
    "fraction_over_precip_thresh": {"pr_per": 95},
    "cold_and_dry_days": {"pr_per": 25, "tas_per": 25},
    "warm_and_dry_days": {"pr_per": 25, "tas_per": 75},
    "warm_and_wet_days": {"pr_per": 75, "tas_per": 75},
    "cold_and_wet_days": {"pr_per": 75, "tas_per": 25},
    "tg90p": {"tas_per": 90},
    "tg10p": {"tas_per": 10},
    "tn90p": {"tasmin_per": 90},
    "tn10p": {"tasmin_per": 10},
    "tx90p": {"tasmax_per": 90},
    "tx10p": {"tasmax_per": 10},
    "cold_spell_duration_index": {"tasmin_per": 10},
    "warm_spell_duration_index": {"tasmax_per": 90},
}


class FinchProcess(Process):
    """Finch Process."""

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
        try:
            return self.wrapped_handler(request, response)
        except Exception as err:
            LOGGER.exception("FinchProcess handler wrapper failed with:")
            raise ProcessError(f"Finch failed with {err!s}")

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
    """Finch ProgressBar."""

    def __init__(
        self, logging_function, start_percentage=0, end_percentage=100, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        # In rare cases writing to stdout causes bugs on binder
        # Here we write to an in-memory file
        self._file = io.StringIO()
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
    # Sanitize name
    name = xci.identifier.replace("{", "_").replace("}", "_").replace("__", "_")

    process_class = type(
        str(name) + class_name_suffix,
        (base_class,),
        {"xci": xci, "__doc__": xci.abstract},
    )

    process = process_class()
    process.translations = {  # type: ignore
        locale: xclim.core.locales.get_local_attrs(
            xci.identifier.upper(), locale, append_locale_name=False
        )
        for locale in xclim.core.locales.list_locales()
    }

    return process  # type: ignore


def convert_xclim_inputs_to_pywps(
    params: Dict, parent=None, parse_percentiles: bool = False
) -> List[PywpsInput]:
    r"""Convert xclim indicators properties to pywps inputs.

    If parse_percentiles is True, percentile variables (\*_per) are dropped and replaced by
    a "percentile" input (a float) with a default taken from constants.
    """
    # Ideally this would be based on the Parameters docstring section rather than name conventions.
    inputs = []
    var_names = []
    # Mapping from xclim's InputKind to data_type
    # Only for generic types
    data_types = {
        InputKind.BOOL: "boolean",
        InputKind.QUANTIFIED: "string",
        InputKind.NUMBER: "integer",
        InputKind.NUMBER_SEQUENCE: "integer",
        InputKind.STRING: "string",
        InputKind.DAY_OF_YEAR: "string",
        InputKind.DATE: "datetime",
    }

    if parse_percentiles and parent is None:
        raise ValueError(
            "The indicator identifier must be passed through `parent` if `parse_percentiles=True`."
        )

    for name, attrs in params.items():
        if (
            parse_percentiles
            and name.endswith("_per")
            and attrs["kind"] in [InputKind.VARIABLE, InputKind.OPTIONAL_VARIABLE]
        ):
            var_name = name.split("_")[0]
            inputs.append(
                LiteralInput(
                    f"perc_{var_name}",
                    title=f"{var_name} percentile",
                    abstract=f"Which percentile to compute and use as threshold for variable {var_name}.",
                    data_type="integer",
                    min_occurs=0,
                    max_occurs=1,
                    default=default_percentiles[parent][name],
                )
            )
        elif attrs["kind"] in [InputKind.VARIABLE, InputKind.OPTIONAL_VARIABLE]:
            inputs.append(make_nc_input(name))
            var_names.append(name)
        elif name in ["freq"]:
            inputs.append(
                make_freq(name, default=attrs["default"], abstract=attrs["description"])
            )
        elif name in ["indexer"]:
            inputs.append(make_month())
            inputs.append(make_season())
        elif attrs["kind"] in data_types:
            choices = list(attrs["choices"]) if "choices" in attrs else None
            default = attrs["default"] if attrs["default"] != empty_default else None
            inputs.append(
                LiteralInput(
                    name,
                    title=name.capitalize().replace("_", " "),
                    abstract=attrs["description"],
                    data_type=data_types[attrs["kind"]],
                    min_occurs=0,
                    max_occurs=1 if attrs["kind"] != InputKind.NUMBER_SEQUENCE else 99,
                    default=default,
                    allowed_values=choices,
                )
            )
        elif attrs["kind"] < 50:
            # raise NotImplementedError(f"{parent}: {name}")
            LOGGER.warning(
                f"{parent}: Argument {name} of kind {attrs['kind']} is not implemented."
            )

    return inputs, var_names


def make_freq(
    name, default="YS", abstract="", allowed=("YS", "MS", "QS-DEC", "AS-JUL")
):  # noqa: D103
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


def make_nc_input(name):  # noqa: D103
    desc = xclim.core.utils.VARIABLES.get(name, {}).get("description", "")
    return ComplexInput(
        name,
        "Resource",
        abstract="NetCDF Files or archive (tar/zip) containing netCDF files. " + desc,
        metadata=[Metadata("Info")],
        min_occurs=1,
        max_occurs=10000,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    )


def make_month():  # noqa: D103
    return LiteralInput(
        identifier="month",
        title="Select by month",
        abstract="Months of the year over which to compute indicator.",
        data_type="integer",
        min_occurs=0,
        max_occurs=12,
        allowed_values=list(range(1, 13)),
    )


def make_season():  # noqa: D103
    return LiteralInput(
        identifier="season",
        title="Select by season",
        abstract="Climatological season over which to compute indicator.",
        data_type="string",
        min_occurs=0,
        max_occurs=1,
        allowed_values=["DJF", "MAM", "JJA", "SON"],
    )
