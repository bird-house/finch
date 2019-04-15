from pywps import Process, LiteralInput, ComplexInput, ComplexOutput, FORMATS
import xarray as xr
from xclim.utils import subset_bbox


class SubsetBboxProcess(Process):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            ComplexInput('resource',
                         'NetCDF resource',
                         abstract='NetCDF files, can be OPEnDAP urls.',
                         max_occurs=1,
                         supported_formats=[FORMATS.NETCDF, FORMATS.DODS]),
            LiteralInput('lon0',
                         'Minimum longitude',
                         abstract='Minimum longitude.',
                         data_type='float',
                         default=0,
                         min_occurs=0,),
            LiteralInput('lon1',
                         'Maximum longitude',
                         abstract='Maximum longitude.',
                         data_type='float',
                         default=360,
                         min_occurs=0,),
            LiteralInput('lat0',
                         'Minimum latitude',
                         abstract='Minimum latitude.',
                         data_type='float',
                         default=-90,
                         min_occurs=0,),
            LiteralInput('lat1',
                         'Maximum latitude',
                         abstract='Maximum latitude.',
                         data_type='float',
                         default=90,
                         min_occurs=0,),
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
                                   'Will be guessed if not provided.'),
                         data_type='string',
                         min_occurs=0)]

        outputs = [
            ComplexOutput('output',
                          'netCDF output',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
        ]

        super(SubsetBboxProcess, self).__init__(
            self._handler,
            identifier='subset_bbox',
            title='Subset',
            version='0.1',
            abstract=('Return the data for which grid cells intersect the '
                      'bounding box for each input dataset as well as'
                      'the time range selected.'),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        # This does not work for multiple input files.
        files = [r.data for r in request.inputs['resource']]
        lon0 = request.inputs['lon0'][0].data
        lon1 = request.inputs['lon1'][0].data
        lat0 = request.inputs['lat0'][0].data
        lat1 = request.inputs['lat1'][0].data
        dt0 = request.inputs['dt0'][0].data or None
        dt1 = request.inputs['dt1'][0].data or None
        vars = [r.data for r in request.inputs['variable']]

        if len(files) > 1:
            raise NotImplementedError

        for i, f in enumerate(files):
            ds = xr.open_dataset(f)
            if vars:
                ds = ds[vars]
            out = subset_bbox(ds, lon_bnds=(lon0, lon1), lat_bnds=(lat0, lat1), start_yr=dt0, end_yr=dt1)
            out.to_netcdf(self.workdir + '/out.nc')
            response.outputs['output'].file = self.workdir + '/out_{}.nc'.format(i)

        return response
