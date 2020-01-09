import os

from finch.processes.base import FinchProgress
from .base import FinchProcess
from pywps import ComplexInput, ComplexOutput, FORMATS, LiteralInput
from pywps.app.Common import Metadata
from unidecode import unidecode
import logging

LOGGER = logging.getLogger("PYWPS")


def make_xclim_indicator_process(xci):
    """Create a WPS Process subclass from an xclim `Indicator` class instance."""
    attrs = xci.json()

    # Sanitize name
    name = attrs['identifier'].replace('{', '_').replace('}', '_').replace('__', '_')

    process_class = type(str(name) + 'Process', (_XclimIndicatorProcess,), {'xci': xci, '__doc__': attrs['abstract']})

    return process_class()


class _XclimIndicatorProcess(FinchProcess):
    """Dummy xclim indicator process class.

    Set xci to the xclim indicator in order to have a working class"""
    xci = None

    def __init__(self):
        """Create a WPS process from an xclim indicator class instance."""

        if self.xci is None:
            raise AttributeError("Use the `make_xclim_indicator_process` function instead.")

        attrs = self.xci.json()

        outputs = [
            ComplexOutput('output_netcdf', 'Function output in netCDF',
                          abstract="The indicator values computed on the original input grid.",
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF, ]  # To support FORMATS.DODS we need to get the URL.
                          ),

            ComplexOutput('output_log', 'Logging information',
                          abstract="Collected logs during process run.",
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT]),
        ]

        identifier = attrs['identifier']
        super(_XclimIndicatorProcess, self).__init__(
            self._handler,
            identifier=identifier,
            version='0.1',
            title=unidecode(attrs['long_name']),
            abstract=unidecode(attrs['abstract']),
            inputs=self.load_inputs(eval(attrs['parameters'])),
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def load_inputs(self, params):
        # Ideally this would be based on the Parameters docstring section rather than name conventions.
        inputs = []

        for name, attrs in params.items():
            if name in ['tas', 'tasmin', 'tasmax', 'pr', 'prsn']:
                inputs.append(make_nc_input(name))
            elif name in ['tn10', 'tn90', 't10', 't90']:
                inputs.append(make_nc_input(name))
            elif name in ['thresh_tasmin', 'thresh_tasmax']:
                inputs.append(make_thresh(name, attrs['default'], attrs['desc']))
            elif name in ['thresh', ]:
                inputs.append(make_thresh(name, attrs['default'], attrs['desc']))
            elif name in ['freq', ]:
                inputs.append(make_freq(name, attrs['default']))
            elif name in ['window', ]:
                inputs.append(make_window(name, attrs['default'], attrs['desc']))
            else:
                # raise NotImplementedError(name)
                LOGGER.warning("not implemented: {}".format(name))

        return inputs

    def _handler(self, request, response):
        self.write_log("Processing started", response, 5)
        out = self.compute_indices(self.xci, request.inputs)

        out_fn = os.path.join(self.workdir, 'out.nc')

        self.write_log("Computing the output netcdf", response, 10)

        def write_log(message, percentage):
            self.write_log(message, response, percentage)

        with FinchProgress(write_log, start_percentage=10, width=15, dt=1):
            out.to_netcdf(out_fn)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs['output_netcdf'].file = out_fn
        response.outputs['output_log'].file = self.log_file_path()
        return response


def make_freq(name, default='YS', allowed=('YS', 'MS', 'QS-DEC', 'AS-JUL')):
    return LiteralInput(name, 'Frequency',
                        abstract='Resampling frequency',
                        data_type='string',
                        min_occurs=0,
                        max_occurs=1,
                        default=default,
                        allowed_values=allowed)


def make_thresh(name, default, abstract=''):
    return LiteralInput(name, 'threshold',
                        abstract=abstract,
                        data_type='string',
                        min_occurs=0,
                        max_occurs=1,
                        default=default,
                        )


def make_window(name, default, abstract=''):
    return LiteralInput(name, 'window',
                        abstract=abstract,
                        data_type='integer',
                        min_occurs=0,
                        max_occurs=1,
                        default=default,
                        )


def make_nc_input(name):
    return ComplexInput(name, 'Resource',
                        abstract='NetCDF Files or archive (tar/zip) containing netCDF files.',
                        metadata=[Metadata('Info')],
                        min_occurs=1,
                        max_occurs=1,
                        supported_formats=[FORMATS.NETCDF])
