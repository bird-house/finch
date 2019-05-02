from pywps import LiteralInput, ComplexInput, ComplexOutput, FORMATS
from pywps.inout.outputs import MetaFile, MetaLink4
from xclim.utils import subset_gridpoint
from pathlib import Path
from .base import FinchProcess


class SubsetGridPointProcess(FinchProcess):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "NetCDF resource",
                abstract="NetCDF files, can be OPEnDAP urls.",
                max_occurs=1000,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            LiteralInput(
                "lon",
                "Longitude",
                abstract="Longitude coordinate",
                data_type="float",
                min_occurs=1,
            ),
            LiteralInput(
                "lat",
                "Latitude",
                abstract="Latitude coordinate.",
                data_type="float",
                min_occurs=1,
            ),
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
            LiteralInput(
                "year0",
                "Initial year",
                abstract="Initial year for temporal subsetting. Defaults to first year in file.",
                data_type="integer",
                default=None,
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "year1",
                "Final year",
                abstract="Final year for temporal subsetting. Defaults to last year in file.",
                data_type="integer",
                default=None,
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "variable",
                "Variable",
                abstract=(
                    "Name of the variable in the NetCDF file."
                    "If not provided, all variables will be subsetted."
                ),
                data_type="string",
                default=None,
                min_occurs=0,
            ),
        ]

        outputs = [
            ComplexOutput(
                "output",
                "netCDF output",
                as_reference=True,
                supported_formats=[FORMATS.NETCDF],
            ),
            ComplexOutput(
                "ref",
                "Link to all output files",
                abstract="Metalink file storing all references to output file.",
                as_reference=False,
                supported_formats=[FORMATS.META4],
            ),
        ]

        super(SubsetGridPointProcess, self).__init__(
            self._handler,
            identifier="subset_gridpoint",
            title="Subset",
            version="0.1",
            abstract=(
                "Return the data for which grid cells includes the "
                "point coordinates for each input dataset as well as"
                "the time range selected."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        self.sentry_configure_scope(request)

        self.write_log("Processing started", response, 5)

        lon = request.inputs["lon"][0].data
        lat = request.inputs["lat"][0].data
        # dt0 = request.inputs['dt0'][0].data or None
        # dt1 = request.inputs['dt1'][0].data or None
        y0 = request.inputs["y0"][0].data or None
        y1 = request.inputs["y1"][0].data or None

        variables = [r.data for r in request.inputs.get("variable", [])]

        metalink = MetaLink4(
            identity="subset_bbox",
            description="Subsetted netCDF files",
            publisher="Finch",
            workdir=self.workdir,
        )

        n_files = len(request.inputs["resource"])

        for n, res in enumerate(request.inputs["resource"]):
            percentage = 5 + n // n_files * (99 - 5)
            self.write_log(f"Processing file {n + 1} of {n_files}", response, percentage)

            ds = self.try_opendap(res)
            if variables:
                ds = ds[variables]

            out = subset_gridpoint(ds, lon=lon, lat=lat, start_yr=y0, end_yr=y1)

            p = Path(res._file or res._build_file_name(res.url))
            out_fn = Path(self.workdir) / (p.stem + "_sub" + p.suffix)
            out.to_netcdf(out_fn)

            mf = MetaFile(
                identity=p.stem,
                description="Subset of file at lon={}, lat={}".format(lon, lat),
                fmt=FORMATS.NETCDF,
            )
            mf.file = out_fn
            metalink.append(mf)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["output"].file = metalink.files[0]
        response.outputs["ref"].data = metalink.xml

        return response
