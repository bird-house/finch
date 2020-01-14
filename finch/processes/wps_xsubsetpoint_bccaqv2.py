from pathlib import Path
from pywps.response.execute import ExecuteResponse
from pywps.app.exceptions import ProcessError
from pywps.app import WPSRequest
from .wpsio import start_date, end_date
from pywps import LiteralInput, ComplexOutput, FORMATS, configuration

from finch.processes import SubsetGridPointProcess
from finch.processes.subset import SubsetProcess
from finch.processes.utils import get_bccaqv2_inputs, netcdf_to_csv, zip_files


class SubsetGridPointBCCAQV2Process(SubsetGridPointProcess):
    """Subset a NetCDF file grid cells using a list of coordinates."""

    def __init__(self):
        inputs = [
            LiteralInput(
                "variable",
                "NetCDF Variable",
                abstract=(
                    "Name of the variable in the NetCDF file."
                    "If not provided, all variables will be subsetted."
                ),
                data_type="string",
                default=None,
                min_occurs=0,
                allowed_values=["tasmin", "tasmax", "pr"],
            ),
            LiteralInput(
                "rcp",
                "RCP Scenario",
                abstract="Representative Concentration Pathway (RCP)",
                data_type="string",
                default=None,
                min_occurs=0,
                allowed_values=["rcp26", "rcp45", "rcp85"],
            ),
            LiteralInput(
                "lat",
                "Latitude",
                abstract="Latitude. Accepts a comma separated list of floats for multiple grid cells.",
                data_type="string",
                min_occurs=0,  # Set to 1 when lat0 is removed
            ),
            LiteralInput(
                "lon",
                "Longitude",
                abstract="Longitude. Accepts a comma separated list of floats for multiple grid cells.",
                data_type="string",
                min_occurs=0,  # Set to 1 when lon0 is removed
            ),
            LiteralInput(
                "lat0",
                "Latitude (deprecated, use 'lat')",
                abstract=(
                    "Latitude (deprecated, use 'lat'). Accepts a comma "
                    "separated list of floats for multiple grid cells."
                ),
                data_type="string",
                min_occurs=0,
            ),
            LiteralInput(
                "lon0",
                "Longitude (deprecated, use 'lon')",
                abstract=(
                    "Latitude (deprecated, use 'lon'). Accepts a comma "
                    "separated list of floats for multiple grid cells."
                ),
                data_type="string",
                min_occurs=0,
            ),
            start_date,
            end_date,
            LiteralInput(
                "output_format",
                "Output format choice",
                abstract="Choose in which format you want to recieve the result",
                data_type="string",
                allowed_values=["netcdf", "csv"],
                default="netcdf",
                min_occurs=0,
            ),
        ]

        outputs = [
            ComplexOutput(
                "output",
                "Result",
                abstract="The format depends on the input parameter 'output_format'",
                as_reference=True,
                supported_formats=[FORMATS.NETCDF, FORMATS.TEXT],
            )
        ]

        SubsetProcess.__init__(
            self,
            self._handler,
            identifier="subset_ensemble_BCCAQv2",
            title="Subset of BCCAQv2 datasets grid cells using a list of coordinates",
            version="0.2",
            abstract=(
                "For the BCCAQv2 datasets, "
                "return the closest grid cell for each provided coordinates pair, "
                "for the time range selected."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request: WPSRequest, response: ExecuteResponse):
        self.write_log("Processing started", response, 5)

        # Temporary backward-compatibility adjustment.
        # Remove me when lon0 and lat0 are removed
        lon, lat, lon0, lat0 = [
            self.get_input_or_none(request.inputs, var)
            for var in "lon lat lon0 lat0".split()
        ]
        if not (lon and lat or lon0 and lat0):
            raise ProcessError("Provide both lat and lon or both lon0 and lat0.")
        request.inputs.setdefault("lon", request.inputs.get("lon0"))
        request.inputs.setdefault("lat", request.inputs.get("lat0"))
        # End of 'remove me'

        # Build output filename
        variable = self.get_input_or_none(request.inputs, "variable")
        rcp = self.get_input_or_none(request.inputs, "rcp")
        lat = self.get_input_or_none(request.inputs, "lat").split(",")[0]
        lon = self.get_input_or_none(request.inputs, "lon").split(",")[0]
        output_format = request.inputs["output_format"][0].data
        output_filename = f"BCCAQv2_subset_grid_cells_{float(lat):.3f}_{float(lon):.3f}"

        self.write_log("Fetching BCCAQv2 datasets", response, 6)
        request.inputs = get_bccaqv2_inputs(request.inputs, variable, rcp)

        self.write_log("Running subset", response, 7)

        threads = int(configuration.get_config_value("finch", "subset_threads"))

        metalink = self.subset(
            request.inputs,
            response,
            start_percentage=7,
            end_percentage=90,
            threads=threads,
        )

        if not metalink.files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        self.write_log("Subset done, creating zip file", response)

        output_files = [mf.file for mf in metalink.files]

        if output_format == "csv":
            csv_files, metadata_folder = netcdf_to_csv(
                output_files,
                output_folder=Path(self.workdir),
                filename_prefix=output_filename,
            )
            output_files = csv_files + [metadata_folder]

        output_zip = Path(self.workdir) / (output_filename + ".zip")

        def log(message_, percentage_):
            self.write_log(message_, response, percentage_)

        zip_files(output_zip, output_files, log_function=log, start_percentage=90)
        response.outputs["output"].file = output_zip

        self.write_log("Processing finished successfully", response, 99)
        return response
