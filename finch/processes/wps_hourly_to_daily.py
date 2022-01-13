from pywps import ComplexInput, ComplexOutput, FORMATS

import logging
from pathlib import Path
from .wps_base import FinchProcess
from . import wpsio
from .utils import log_file_path, write_log, try_opendap, dataset_to_netcdf
from xclim.core.formatting import update_history, merge_attributes
import xarray as xr

LOGGER = logging.getLogger("PYWPS")
import json
from xclim.core.options import MISSING_METHODS


class HourlyToDailyProcess(FinchProcess):
    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "Resource",
                abstract="NetCDF file with time series at hourly frequency.",
                min_occurs=1,
                max_occurs=1,
                supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
            ),
            wpsio.reducer,
            wpsio.check_missing,
            wpsio.missing_options,
            wpsio.variable_any,
        ]

        outputs = [
            ComplexOutput(
                "output_netcdf",
                "Daily statistic in netCDF",
                abstract="The daily statistic computed from hourly data.",
                as_reference=True,
                supported_formats=[
                    FORMATS.NETCDF,
                ],
            ),
            wpsio.output_log,
        ]

        super().__init__(
            self._handler,
            identifier="hourly_to_daily",
            version="0.1",
            title="Resample from hourly frequency to daily frequency.",
            abstract="Take the mean, sum, minimum or maximum of hourly data over each day to compute daily values.",
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {
            "start": 5,
            "done": 99,
        }

    def _handler(self, request, response):
        write_log(self, "Processing started", process_step="start")

        # --- Process inputs ---
        resource = request.inputs["resource"][0]
        variables = [r.data for r in request.inputs.get("variable", [])]
        reducer = request.inputs["reducer"][0].data
        check_missing = request.inputs["check_missing"][0].data
        missing_options = json.loads(request.inputs["missing_options"][0].data)

        # Open netCDF file or link
        ds = try_opendap(resource)
        ds = ds[variables] if variables else ds

        # --- Do the resampling computation ---
        out = _hourly_to_daily(ds, reducer=reducer, check_missing=check_missing, missing_options=missing_options)

        # Write to disk
        output_file = Path(self.workdir) / "daily.nc"
        dataset_to_netcdf(out, output_file)

        # Fill response
        response.outputs["output_netcdf"].file = str(output_file)
        response.outputs["output_log"].file = str(log_file_path(self))


def _hourly_to_daily(ds: xr.Dataset, reducer: str, check_missing: str, missing_options: dict) -> xr.Dataset:
    """Convert an hourly time series to a daily time series."""

    # Validate missing values algorithm options
    kls = MISSING_METHODS[check_missing]
    missing = kls.execute
    if missing_options:
        kls.validate(**missing_options)

    # Resample to daily
    out = getattr(ds.resample(time="D"), reducer)(keep_attrs=True)

    # Update and format attributes
    for key, da in out.data_vars.items():
        # Update cell_methods
        da.attrs["cell_methods"] = (
            da.attrs.get("cell_methods", " ") + f" time: {reducer}"
        ).strip()

        # Update history
        da.attrs["history"] = update_history(
            f"Reduce hourly data to daily using {reducer}.", da
        )

    # Compute missing values mask
    if check_missing != "skip":
        for key, da in ds.data_vars.items():
            mask = missing(
                da, freq="D", src_timestep="H", options=missing_options, indexer={}
            )
            out[key] = out[key].where(~mask)

    return out
