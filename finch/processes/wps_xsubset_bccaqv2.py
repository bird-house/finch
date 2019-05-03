import os
import zipfile
from copy import deepcopy

from pathlib import Path
from pywps import LiteralInput, ComplexInput, ComplexOutput, FORMATS, Process

from finch.processes import SubsetBboxProcess
from finch.processes.utils import get_opendap_datasets


class SubsetBCCAQV2Process(SubsetBboxProcess):
    """Subset a NetCDF file using bounding box geometry."""

    bccaqv2_link = "https://boreas.ouranos.ca/thredds/catalog/birdhouse/pcic/BCCAQv2/catalog.xml"

    def __init__(self):
        inputs = [
            LiteralInput(
                "rcp",
                "RCP Scenario",
                abstract="Representative Concentration Pathway (RCP)",
                data_type="string",
                allowed_values=["rcp26", "rcp45", "rcp85"],
            ),
            LiteralInput(
                "variable",
                "NetCDF Variable",
                abstract="Name of the variable in the NetCDF file.",
                data_type="string",
                allowed_values=["tasmin", "tasmax", "pr"],
            ),
            ComplexInput(
                "resource",
                "NetCDF resource",
                abstract=(
                    "NetCDF files, can be OPEnDAP urls."
                    "If missing, the process will scan all BBBAQv2 data."
                ),
                min_occurs=0,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            LiteralInput(
                "lon0",
                "Minimum longitude",
                abstract="Minimum longitude.",
                data_type="float",
                default=0,
                min_occurs=0,
            ),
            LiteralInput(
                "lon1",
                "Maximum longitude",
                abstract="Maximum longitude.",
                data_type="float",
                default=360,
                min_occurs=0,
            ),
            LiteralInput(
                "lat0",
                "Minimum latitude",
                abstract="Minimum latitude.",
                data_type="float",
                default=-90,
                min_occurs=0,
            ),
            LiteralInput(
                "lat1",
                "Maximum latitude",
                abstract="Maximum latitude.",
                data_type="float",
                default=90,
                min_occurs=0,
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
                "y0",
                "Initial year",
                abstract="Initial year for temporal subsetting. Defaults to first year in file.",
                data_type="integer",
                default=None,
                min_occurs=0,
            ),
            LiteralInput(
                "y1",
                "Final year",
                abstract="Final year for temporal subsetting. Defaults to last year in file.",
                data_type="integer",
                min_occurs=0,
            ),
        ]

        outputs = [
            ComplexOutput(
                "zip",
                "Zip file",
                abstract="A zip file containing all the output files.",
                as_reference=True,
                supported_formats=[FORMATS.ZIP],
            )
        ]

        Process.__init__(
            self,
            self._handler,
            identifier="subset_ensemble_BCCAQv2",
            title="Subset of BCCAQv2 datasets",
            version="0.1",
            abstract=(
                "For the BCCAQv2 datasets, "
                "return the data for which grid cells intersect the "
                "bounding box for each input dataset as well as "
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
        self.write_log("Reading inputs", response, 5)

        variable = request.inputs["variable"][0].data
        rcp = request.inputs["rcp"][0].data

        if "resource" not in request.inputs:
            request.inputs["resource"] = []

            resource_input = [r for r in self.inputs if r.identifier == "resource"][0]

            self.write_log("Fetching BCCAQv2 datasets", response, 6)
            for url in get_opendap_datasets(self.bccaqv2_link, variable, rcp):
                input_ = deepcopy(resource_input)
                input_.url = url
                request.inputs["resource"].append(input_)

        self.write_log("Running subset", response, 7)
        metalink = self.subset(request.inputs, response, start_percentage=7, end_percentage=85)
        self.write_log("Subset done, crating zip file", response, 85)

        output_filename = Path(self.workdir) / f"BCCAQv2_subset_{rcp}_{variable}.zip"

        with zipfile.ZipFile(output_filename, mode="w") as z:
            n_files = len(metalink.files)
            for n, mf in enumerate(metalink.files):
                percentage = 85 + n // n_files * 14
                self.write_log(f"Zipping file {n + 1} of {n_files}", response, percentage)
                z.write(mf.file, arcname=Path(mf.file).name)

        self.write_log("Processing finished successfully", response, 99)

        response.outputs["zip"].file = output_filename
        return response
