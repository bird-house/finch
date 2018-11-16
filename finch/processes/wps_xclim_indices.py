from pywps import Process
from pywps import ComplexInput, ComplexOutput, FORMATS, LiteralInput
from pywps.app.Common import Metadata
# import eggshell.general.utils
# from eggshell.log import init_process_logger

import xarray as xr
import os
import logging
LOGGER = logging.getLogger("PYWPS")


class UnivariateXclimIndicatorProcess(Process):

    def __init__(self, xci):
        """Create a WPS process from an xclim indicator class instance."""
        self.xci = xci
        self.varname = None

        attrs = xci.json

        outputs = [
            ComplexOutput('output_netcdf', 'Function output in netCDF',
                          abstract="The indicator values computed on the original input grid.",
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]
                          ),

            ComplexOutput('output_log', 'Logging information',
                          abstract="Collected logs during process run.",
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT]),
        ]

        super(UnivariateXclimIndicatorProcess, self).__init__(
            self._handler,
            identifier=attrs['identifier'],
            version='0.1',
            title=attrs['long_name'],
            abstract=attrs['abstract'],
            inputs=self.load_inputs(attrs['parameters']),
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
                self.varname = name
            elif name in ['tn10', 'tn90']:
                inputs.append(make_nc_input(name))
            elif name in ['thresh_tasmin', 'thresh_tasmax']:
                inputs.append(make_nc_input(name))
            elif name in ['thresh', ]:
                inputs.append(make_thresh(name, attrs['default'], attrs['desc']))
            elif name in ['freq', ]:
                inputs.append(make_freq(name, attrs['default']))
            elif name in ['window', ]:
                # TODO: does not work
                # inputs.append(make_window(name, attrs['default'], attrs['desc']))
                pass
            else:
                # raise NotImplementedError(name)
                LOGGER.warning("not implemented: {}".format(name))

        return inputs

    def _handler(self, request, response):
        # init_process_logger('log.txt')
        with open(os.path.join(self.workdir, 'log.txt'), 'w') as fp:
            fp.write('not used ... sorry.\n')
            response.outputs['output_log'].file = fp.name

        # Process inputs
        kwds = {}
        for name, obj in request.inputs.items():
            if isinstance(obj[0], ComplexInput):
                fn = obj[0].file  # eggshell.general.utils.archiveextract(resource=eggshell.general.utils.rename_complexinputs(obj)) # noqa
                ds = xr.open_mfdataset(fn)
                kwds[name] = ds.data_vars[self.varname]

            elif isinstance(obj[0], LiteralInput):
                kwds[name] = obj[0].data

        # Run the computation
        out = self.xci(**kwds)

        # Store the output
        out_fn = os.path.join(self.workdir, 'out.nc')
        out.to_netcdf(out_fn)
        response.outputs['output_netcdf'].file = out_fn
        return response


def make_freq(name, default='YS', allowed=('YS', 'MS', 'QS-DEC')):
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
                        data_type='float',
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
                        max_occurs=1000,
                        supported_formats=[FORMATS.NETCDF])
