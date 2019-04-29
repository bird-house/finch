from pywps import LiteralInput, ComplexInput, ComplexOutput, FORMATS
from xclim.utils import subset_bbox
from pathlib import Path
from pywps.inout.outputs import MetaFile, MetaLink4
from .base import FinchProcess


class SubsetBboxProcess(FinchProcess):
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

        lon0 = request.inputs['lon0'][0].data
        lon1 = request.inputs['lon1'][0].data
        lat0 = request.inputs['lat0'][0].data
        lat1 = request.inputs['lat1'][0].data
        # dt0 = request.inputs['dt0'][0].data or None
        # dt1 = request.inputs['dt1'][0].data or None
        y0 = request.inputs['y0'][0].data or None
        y1 = request.inputs['y1'][0].data or None
        if 'variable' in request.inputs:
            vars = [r.data for r in request.inputs['variable']]
        else:
            vars = None

        meta = MetaLink4('subset_bbox', "Subsetted netCDF files", "Finch", workdir=self.workdir)

        for i, res in enumerate(request.inputs['resource']):

            ds = self.try_opendap(res)
            if vars:
                ds = ds[vars]

            out = subset_bbox(ds, lon_bnds=[lon0, lon1], lat_bnds=[lat0, lat1], start_yr=y0, end_yr=y1)

            p = Path(res._file or res._build_file_name(res.url))
            out_fn = Path(self.workdir) / (p.stem + '_sub' + p.suffix)
            out.to_netcdf(out_fn)

            # Save first file to output
            if i == 0:
                response.outputs['output'].file = out_fn

            # Metalink reference for all other files
            mf = MetaFile(identity=p.stem,
                          description="Subset of file on bounding box lon=({}, {}) lat=({}, {})".format(lon0, lon1,
                                                                                                        lat0, lat1),
                          fmt=FORMATS.NETCDF)
            mf.file = out_fn
            meta.append(mf)

        return response
