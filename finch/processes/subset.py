import logging
from multiprocessing.pool import ThreadPool
from pathlib import Path

from pywps import FORMATS
from pywps.inout.outputs import MetaLink4, MetaFile

from finch.processes.base import FinchProcess

LOGGER = logging.getLogger("PYWPS")


class SubsetProcess(FinchProcess):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def subset_resources(self, resources, subset_function, threads=1) -> MetaLink4:
        metalink = MetaLink4(
            identity="subset_bbox",
            description="Subsetted netCDF files",
            publisher="Finch",
            workdir=self.workdir,
        )

        def process_resource(resource):
            out = subset_function(resource)

            if not all(out.dims.values()):
                LOGGER.warning(f"Subset is empty for dataset: {resource.url}")
                return

            p = Path(resource._file or resource._build_file_name(resource.url))
            out_fn = Path(self.workdir) / (p.stem + "_sub" + p.suffix)

            out.to_netcdf(out_fn)

            mf = MetaFile(
                identity=p.stem,
                fmt=FORMATS.NETCDF,
            )
            mf.file = str(out_fn)
            metalink.append(mf)

        # Loop through all resources
        if threads > 1:
            pool = ThreadPool(processes=threads)
            list(pool.imap_unordered(process_resource, resources))
            pool.close()
            pool.join()
        else:
            for r in resources:
                process_resource(r)

        return metalink

    def get_shape(self, wps_inputs):
        return wps_inputs['shape'][0].data

    def subset(self, wps_inputs, response, start_percentage=10, end_percentage=85, threads=1) -> MetaLink4:
        """Subclass"""

    def _handler(self, request, response):
        self.write_log("Processing started", response, 5)

        metalink = self.subset(request.inputs, response)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["output"].file = metalink.files[0].file
        response.outputs["ref"].data = metalink.xml

        return response
