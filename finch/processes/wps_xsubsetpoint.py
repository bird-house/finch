from pywps import Process, LiteralInput, ComplexInput, ComplexOutput, FORMATS
from pywps.inout.outputs import MetaFile, MetaLink4
import xarray as xr
from xclim.utils import subset_gridpoint
from pathlib import Path


class SubsetGridPointProcess(Process):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            ComplexInput('resource',
                         'NetCDF resource',
                         abstract='NetCDF files, can be OPEnDAP urls.',
                         max_occurs=1000,
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
            # LiteralInput('dt0',
            #              'Initial datetime',
            #              abstract='Initial datetime for temporal subsetting. Defaults to first date in file.',
            #              data_type='dateTime',
            #              default=None,
            #              min_occurs=0,
            #              max_occurs=1),
            # LiteralInput('dt1',
            #              'Final datetime',
            #              abstract='Final datetime for temporal subsetting. Defaults to last date in file.',
            #              data_type='dateTime',
            #              default=None,
            #              min_occurs=0,
            #              max_occurs=1),
            LiteralInput('y0',
                         'Initial year',
                         abstract='Initial year for temporal subsetting. Defaults to first year in file.',
                         data_type='integer',
                         default=None,
                         min_occurs=0,
                         max_occurs=1),
            LiteralInput('y1',
                         'Final year',
                         abstract='Final year for temporal subsetting. Defaults to last year in file.',
                         data_type='integer',
                         default=None,
                         min_occurs=0,
                         max_occurs=1),
            LiteralInput('variable',
                         'Variable',
                         abstract=('Name of the variable in the NetCDF file.'
                                   'If not provided, all variables will be subsetted.'),
                         data_type='string',
                         default=None,
                         min_occurs=0)]

        outputs = [
            ComplexOutput('output',
                          'netCDF output',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
            ComplexOutput('ref', 'Link to all output files',
                          abstract="Metalink file storing all references to output file.",
                          as_reference=False,
                          supported_formats=[FORMATS.META4])
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
        files = [r.file for r in request.inputs['resource']]
        lon = request.inputs['lon'][0].data
        lat = request.inputs['lat'][0].data
        # dt0 = request.inputs['dt0'][0].data or None
        # dt1 = request.inputs['dt1'][0].data or None
        y0 = request.inputs['y0'][0].data or None
        y1 = request.inputs['y1'][0].data or None

        if 'variable' in request.inputs:
            vars = [r.data for r in request.inputs['variable']]
        else:
            vars = None

        meta = MetaLink4('subset_gridpoint', "Subsetted netCDF files", "Finch", workdir=self.workdir)

        for i, f in enumerate(files):
            ds = xr.open_dataset(f)
            if vars:
                ds = ds[vars]

            out = subset_gridpoint(ds, lon=lon, lat=lat, start_yr=y0, end_yr=y1)

            p = Path(f)
            out_fn = Path(self.workdir) / (p.stem + '_sub' + p.suffix)
            out.to_netcdf(out_fn)

            # Save first file to output
            if i == 0:
                response.outputs['output'].file = out_fn

            # Metalink reference for all other files
            mf = MetaFile(identity=p.stem,
                          description="Subset of file at lon={}, lat={}".format(lon, lat),
                          fmt=FORMATS.NETCDF)
            mf.file = out_fn
            meta.append(mf)

        response.outputs['ref'].data = meta.xml

        return response
