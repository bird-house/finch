"""
Statistical downscaling and bias adjustment
===========================================

Expose xclim.sdba algorithms as WPS.

For the moment, both train-adjust operations are bundled into a single process.
"""
import logging
import xclim
from pathlib import Path
import string
import traceback
from xclim.core.calendar import convert_calendar
from xclim.sdba.utils import ADDITIVE, MULTIPLICATIVE
from pywps import ComplexInput, LiteralInput, ComplexOutput, FORMATS
from pywps.app.exceptions import ProcessError
from .wps_base import FinchProcess, FinchProgressBar
from . import wpsio

from .utils import (
    RequestInputs,
    process_threaded,
    log_file_path,
    single_input_or_none,
    try_opendap,
    write_log,
    dataset_to_netcdf,
    make_metalink_output,
)

LOGGER = logging.getLogger("PYWPS")

group_args = dict(
    group=LiteralInput(
        "group",
        "Grouping attribute",
        abstract="The usual grouping name as xarray understands it. Ex: `time.month` or `time`.",
        data_type="string",
        default="time",
        min_occurs=0,
    ),
    window=LiteralInput(
        "window",
        "Window length",
        abstract="If larger than 1, a centered rolling window along the main dimension "
        "is created when grouping data."
        "Units are the sampling frequency of the data along the main dimension.",
        data_type="integer",
        default=1,
        min_occurs=0,
    ),
    interp=LiteralInput(
        "interp",
        "Quantile interpolation",
        abstract="Interpolation method to determine the quantile correction factor to apply. ",
        data_type="string",
        default="nearest",
        allowed_values=["nearest", "linear", "cubic"],
        min_occurs=0,
    ),
)
adjust_args = dict(
    extrapolation=LiteralInput(
        "extrapolation",
        "Extrapolation method",
        abstract="Method used to extrapolate quantile adjustment factors beyond the computed quantiles.",
        data_type="string",
        default="constant",
        allowed_values=["constant", "nan"],
        min_occurs=0,
    )
)
variable = wpsio.variable

resources = dict(
    ref=ComplexInput(
        "ref",
        "Reference dataset",
        abstract="Reference netCDF resource, typically observations or reanalyses.",
        max_occurs=1,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    ),
    hist=ComplexInput(
        "hist",
        "Historical simulation",
        abstract="Historical simulation netCDF resource overlapping the reference dataset.",
        max_occurs=1,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    ),
    sim=ComplexInput(
        "sim",
        "Target simulation to be corrected",
        abstract="Simulation netCDF resource whose bias will be corrected",
        max_occurs=1,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    ),
)

common_outputs = [
    ComplexOutput(
        "output",
        "netCDF output",
        as_reference=True,
        supported_formats=[FORMATS.NETCDF],
    ),
    wpsio.output_log,
    wpsio.output_metalink,
]


class EmpiricalQuantileMappingProcess(FinchProcess):
    def __init__(self):
        inputs = (
            list(resources.values())
            + list(group_args.values())
            + list(adjust_args.values())
            + [
                wpsio.variable_any,
                LiteralInput(
                    "nquantiles",
                    "Number of quantile bins",
                    abstract="The number of quantiles to use. Two endpoints at 1e-6 and 1 - 1e-6 will be added.",
                    data_type="integer",
                    default=20,
                    min_occurs=0,
                ),
                LiteralInput(
                    "kind",
                    "Kind of adjustment (+, *)",
                    abstract="Use * for multiplicative adjustment, or + for additive adjustement.",
                    data_type="string",
                    default=ADDITIVE,
                    allowed_values=[ADDITIVE, MULTIPLICATIVE],
                    min_occurs=0,
                ),
            ]
        )

        super().__init__(
            self._handler,
            identifier="empirical_quantile_mapping",
            title="Empirical Quantile Mapping bias-adjustment",
            version="0.1",
            abstract="Adjustment factors are computed between the quantiles of `ref` and `sim`."
            "Values of `sim` are matched to the corresponding quantiles of `hist` and corrected accordingly.",
            inputs=inputs,
            outputs=common_outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        def _log(message, percentage):
            write_log(self, message, subtask_percentage=percentage)

        res = {}
        group = {}
        train = {}
        adj = {}

        variable = request.inputs.pop(wpsio.variable.identifier, None)

        for key, input in request.inputs.items():
            if key in resources:
                ds = try_opendap(request.inputs[key][0])
                name = variable or list(ds.data_vars)[0]

                # Force calendar to noleap
                res[key] = convert_calendar(ds[name], "noleap")

            elif key in group_args:
                group[key] = single_input_or_none(request.inputs, key)

            elif key in adjust_args:
                adj[key] = single_input_or_none(request.inputs, key)

            else:
                train[key] = single_input_or_none(request.inputs, key)

        _log("Successfully read inputs from request.", 1)

        group = xclim.sdba.Grouper(**group)
        _log("Grouper object created.", 2)

        bc = xclim.sdba.EmpiricalQuantileMapping.train(res["ref"], res["hist"], **train, group=group)
        _log("Training object created.", 3)

        out = bc.adjust(res["sim"], interp=group["interp"], **adj).to_dataset(name=name)
        _log("Adjustment object created.", 5)

        out_fn = Path(self.workdir) / "bias_corrected.nc"
        with FinchProgressBar(
            logging_function=_log,
            start_percentage=5,
            end_percentage=98,
            width=15,
            dt=1,
        ):
            dataset_to_netcdf(out, out_fn)

        metalink = make_metalink_output(self, [out_fn])

        response.outputs["output"].file = str(out_fn)
        response.outputs["output_log"].file = str(log_file_path(self))
        response.outputs["ref"].data = metalink.xml

        write_log(self, "Processing finished successfully", process_step="done")

        return response
