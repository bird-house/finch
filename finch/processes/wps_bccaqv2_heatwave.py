import logging
import warnings
from collections import deque
from typing import List, Tuple

import numpy as np
import xarray as xr
from xclim.checks import assert_daily
from xclim.atmos import heat_wave_frequency
from pathlib import Path
from pywps.response.execute import ExecuteResponse
from pywps.app.exceptions import ProcessError
from pywps.app import WPSRequest
from pywps import LiteralInput, ComplexOutput, FORMATS, configuration
import sentry_sdk

from finch.processes import make_xclim_indicator_process, SubsetGridPointProcess
from finch.processes.subset import SubsetProcess
from finch.processes.utils import get_bccaqv2_inputs, netcdf_to_csv, zip_files
from finch.processes.wps_xclim_indices import make_nc_input

LOGGER = logging.getLogger("PYWPS")


class BCCAQV2HeatWave(SubsetGridPointProcess):
    """Subset a NetCDF file using a gridpoint, and then compute the 'heat wave' index."""

    def __init__(self):
        self.indices_process = make_xclim_indicator_process(heat_wave_frequency)
        inputs = [
            i
            for i in self.indices_process.inputs
            if i.identifier not in ["tasmin", "tasmax"]
        ]
        inputs += [
            LiteralInput(
                "lon",
                "Longitude of point",
                abstract="Longitude located inside the grid-cell to extract.",
                data_type="string",
            ),
            LiteralInput(
                "lat",
                "Latitude of point",
                abstract="Latitude located inside the grid-cell to extract.",
                data_type="string",
            ),
            LiteralInput(
                "y0",
                "Initial year",
                abstract="Initial year for temporal subsetting. Defaults to first year in file.",
                data_type="integer",
                min_occurs=0,
            ),
            LiteralInput(
                "y1",
                "Final year",
                abstract="Final year for temporal subsetting. Defaults to last year in file.",
                data_type="integer",
                min_occurs=0,
            ),
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
            identifier="BCCAQv2_heat_wave_frequency_gridpoint",
            title="BCCAQv2 grid cell heat wave frequency computation",
            version="0.1",
            abstract=(
                "Compute heat wave frequency for all the "
                "BCCAQv2 datasets for a single grid cell."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _make_tasmin_tasmax_pairs(self, filenames: List[Path]):
        tasmin_files = [f for f in filenames if "tasmin" in f.name.lower()]
        tasmax_files = [f for f in filenames if "tasmax" in f.name.lower()]
        for tasmin in tasmin_files[:]:
            for tasmax in tasmax_files[:]:
                if tasmin.name.lower() == tasmax.name.lower().replace(
                    "tasmax", "tasmin"
                ):
                    yield tasmin, tasmax
                    tasmax_files.remove(tasmax)
                    tasmin_files.remove(tasmin)
                    break
        for f in tasmax_files + tasmax_files:
            sentry_sdk.capture_message(
                f"Couldn't find matching tasmin or tasmax for: {f}", level="error"
            )

    def _handler(self, request: WPSRequest, response: ExecuteResponse):
        self.write_log("Processing started", response, 5)

        lat = request.inputs["lat"][0].data
        lon = request.inputs["lon"][0].data
        output_format = request.inputs["output_format"][0].data
        output_filename = f"BCCAQv2_subset_heat_wave_frequency_{lat}_{lon}"

        self.write_log("Fetching BCCAQv2 datasets", response, 6)
        tasmin_inputs = get_bccaqv2_inputs(request.inputs, "tasmin")["resource"]
        tasmax_inputs = get_bccaqv2_inputs(request.inputs, "tasmax")["resource"]

        request.inputs["resource"] = tasmin_inputs + tasmax_inputs

        self.write_log("Running subset", response, 7)

        threads = int(configuration.get_config_value("finch", "subset_threads"))

        metalink = self.subset(
            request.inputs,
            response,
            start_percentage=7,
            end_percentage=70,
            threads=threads,
        )

        if not metalink.files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        self.write_log("Subset done, calculating indices", response)

        all_files = [Path(f.file) for f in metalink.files]

        pairs = list(self._make_tasmin_tasmax_pairs(all_files))
        n_pairs = len(pairs)

        start_percentage, end_percentage = 70, 95
        output_files = []

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        for n, (tasmin, tasmax) in enumerate(pairs):
            percentage = start_percentage + int(
                n / n_pairs * (end_percentage - start_percentage)
            )
            self.write_log(
                f"Computing indices for file {n + 1} of {n_pairs}",
                response,
                percentage,
            )

            tasmin, tasmax = fix_broken_time_indices(tasmin, tasmax)

            compute_inputs = [i.identifier for i in self.indices_process.inputs]
            inputs = {k: v for k, v in request.inputs.items() if k in compute_inputs}

            inputs["tasmin"] = deque([make_nc_input("tasmin")], maxlen=1)
            inputs["tasmin"][0].file = str(tasmin)
            inputs["tasmax"] = deque([make_nc_input("tasmax")], maxlen=1)
            inputs["tasmax"][0].file = str(tasmax)

            out = self.compute_indices(self.indices_process.xci, inputs)
            out_fn = Path(self.workdir) / tasmin.name.replace(
                "tasmin", "heat_wave_frequency"
            )
            out.to_netcdf(out_fn)
            output_files.append(out_fn)

        warnings.filterwarnings("default", category=FutureWarning)
        warnings.filterwarnings("default", category=UserWarning)

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


def fix_broken_time_indices(tasmin: Path, tasmax: Path) -> Tuple[Path, Path]:
    """In a single bccaqv2 dataset, there is an error in the timestamp data.

    2036-10-28 time step coded as 1850-01-01
    tasmax_day_BCCAQv2+ANUSPLIN300_CESM1-CAM5_historical+rcp85_r1i1p1_19500101-21001231_sub.nc
    """
    tasmin_ds = xr.open_dataset(tasmin)
    tasmax_ds = xr.open_dataset(tasmax)

    def fix(correct_ds, wrong_ds, original_filename):
        wrong_ds["time"] = correct_ds.time
        temp_name = original_filename.with_name(original_filename.stem + "_temp")
        wrong_ds.to_netcdf(temp_name)
        original_filename.unlink()
        temp_name.rename(original_filename)

    try:
        assert_daily(tasmin_ds)
    except ValueError:
        fix(tasmax_ds, tasmin_ds, tasmin)
        return tasmin, tasmax

    try:
        assert_daily(tasmax_ds)
    except ValueError:
        fix(tasmin_ds, tasmax_ds, tasmax)
        return tasmin, tasmax

    return tasmin, tasmax
