from pywps import Process, LiteralInput, ComplexInput, ComplexOutput, FORMATS
import xarray as xr
from xclim.utils import subset_gridpoint


class SubsetGridPointProcess(Process):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            ComplexInput('resource',
                         'NetCDF resource',
                         abstract='NetCDF files, can be OPEnDAP urls.',
                         max_occurs=1,
                         supported_formats=[FORMATS.NETCDF, FORMATS.DODS]),
            LiteralInput('lon',
                         'Longitude',
                         abstract='Minimum longitude.',
                         data_type='float',
                         min_occurs=1,),
            LiteralInput('lat',
                         'Latitude',
                         abstract='Minimum latitude.',
                         data_type='float',
                         min_occurs=1,),
            LiteralInput('dt0',
                         'Initial datetime',
                         abstract='Initial datetime for temporal subsetting.',
                         data_type='dateTime',
                         default=None,
                         min_occurs=0,
                         max_occurs=1),
            LiteralInput('dt1',
                         'Final datetime',
                         abstract='Final datetime for temporal subsetting.',
                         data_type='dateTime',
                         default=None,
                         min_occurs=0,
                         max_occurs=1),
            LiteralInput('variable',
                         'Variable',
                         abstract=('Name of the variable in the NetCDF file.'
                                   'If not provided, all variables will be subsetted.'),
                         data_type='string',
                         min_occurs=0)]

        outputs = [
            ComplexOutput('output',
                          'netCDF output',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
            ]

        super(SubsetGridPointProcess, self).__init__(
            self._handler,
            identifier='subset_gridpoint',
            title='Subset',
            version='0.1',
            abstract=('Return the data for which grid cells includes the '
                      'point coordinates for each input dataset as well as'
                      'the time range selected.'),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        # This does not work for multiple input files.
        files = [r.data for r in request.inputs['resource']]
        lon = request.inputs['lon'][0].data
        lat = request.inputs['lat'][0].data
        dt0 = request.inputs['dt0'][0].data or None
        dt1 = request.inputs['dt1'][0].data or None
        vars = [r.data for r in request.inputs['variable']]

        if len(files) > 1:
            raise NotImplementedError

        for i, f in enumerate(files):
            ds = xr.open_dataset(f)
            if vars:
                ds = ds[vars]

            out = subset_gridpoint(ds, lon=lon, lat=lat, start_yr=dt0, end_yr=dt1)
            out.to_netcdf(self.workdir + '/out.nc')
            response.outputs['output'].file = self.workdir + '/out_{}.nc'.format(i)

        return response
