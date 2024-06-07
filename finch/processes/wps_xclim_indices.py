# noqa: D100
import logging
from collections import deque
from pathlib import Path
from typing import List, Optional

import pandas as pd
import xarray as xr
from anyascii import anyascii
from pandas.api.types import is_numeric_dtype
from pywps.app.exceptions import ProcessError

from . import wpsio
from .utils import (
    compute_indices,
    dataset_to_dataframe,
    dataset_to_netcdf,
    drs_filename,
    format_metadata,
    log_file_path,
    make_metalink_output,
    single_input_or_none,
    valid_filename,
    write_log,
    zip_files,
)
from .wps_base import FinchProcess, FinchProgressBar, convert_xclim_inputs_to_pywps

LOGGER = logging.getLogger("PYWPS")


class XclimIndicatorBase(FinchProcess):
    """Dummy xclim indicator process class.

    Set xci to the xclim indicator in order to have a working class.
    """

    xci = None

    def __init__(self):
        """Create a WPS process from an xclim indicator class instance."""
        if self.xci is None:
            raise AttributeError(
                "Use the `make_xclim_indicator_process` function instead."
            )

        outputs = [wpsio.output_netcdf_zip, wpsio.output_log, wpsio.output_metalink]

        inputs, varnames = convert_xclim_inputs_to_pywps(
            self.xci.parameters, self.xci.identifier
        )
        self.allvars = varnames
        inputs += wpsio.xclim_common_options
        inputs += [
            wpsio.variable_any,
            wpsio.output_name,
            wpsio.output_format_netcdf_csv,
            wpsio.csv_precision,
        ]

        super().__init__(
            self._handler,
            identifier=self.xci.identifier,
            version="0.1",
            title=anyascii(self.xci.title),
            abstract=anyascii(self.xci.abstract),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {"start": 5, "convert_to_csv": 90, "done": 99}

    def _handler(self, request, response):
        convert_to_csv = single_input_or_none(request.inputs, "output_format") == "csv"
        if not convert_to_csv:
            del self.status_percentage_steps["convert_to_csv"]

        write_log(self, "Computing the output array", process_step="start")

        # Get inputs of compute_indices, split by netCDFs and others
        nc_inputs, other_inputs = {}, {}
        for k, v in request.inputs.items():
            if k in self.allvars:
                nc_inputs[k] = v
            elif k not in ["output_format", "output_name", "csv_precision"]:
                other_inputs[k] = v

        n_files = len(list(nc_inputs.values())[0])

        if not all(n_files == len(v) for v in nc_inputs.values()):
            raise ProcessError(
                f"The count of all netcdf input variables must be equal: {', '.join(nc_inputs)}."
            )

        def _log(message, percentage):
            write_log(self, message, subtask_percentage=percentage)

        output_name = single_input_or_none(request.inputs, "output_name")
        output_files = []
        input_files = [Path(fn[0].url).name for fn in nc_inputs.values()]

        for n in range(n_files):
            # create a dict containing a single netcdf input for each type
            netcdf_inputs = {k: deque([queue[n]]) for k, queue in nc_inputs.items()}
            inputs = {**other_inputs, **netcdf_inputs}

            out = compute_indices(self, self.xci, inputs)
            filename = _make_unique_drs_filename(
                out,
                [f.name for f in output_files] + input_files,
                output_name=output_name,
            )
            output_filename = Path(self.workdir, filename)
            output_files.append(output_filename)

            start_percentage = int(n / n_files * 100)
            end_percentage = int((n + 1) / n_files * 100)
            write_log(
                self,
                f"Processing file {n + 1} of {n_files}",
                subtask_percentage=start_percentage,
            )

            with FinchProgressBar(
                logging_function=_log,
                start_percentage=start_percentage,
                end_percentage=end_percentage,
                width=15,
                dt=1,
            ):
                write_log(self, f"Writing file {output_filename} to disk.")
                dataset_to_netcdf(out, output_filename)
                out.close()

        if convert_to_csv:
            write_log(self, "Converting netCDFs to CSV", process_step="convert_to_csv")
            output_netcdfs = output_files
            output_files = []
            for outfile in output_netcdfs:
                outcsv = outfile.with_suffix(".csv")
                ds = xr.open_dataset(outfile, decode_timedelta=False)
                prec = single_input_or_none(request.inputs, "csv_precision")
                if prec and prec < 0:
                    ds = ds.round(prec)
                    prec = 0
                df = dataset_to_dataframe(ds)
                if prec is not None:
                    for v in df:
                        if v not in ds.coords and is_numeric_dtype(df[v]):
                            df[v] = df[v].map(
                                lambda x: f"{x:.{prec}f}" if not pd.isna(x) else ""
                            )
                df.to_csv(outcsv)
                output_files.append(outcsv)

                metadata = format_metadata(ds)
                outmeta = outfile.with_suffix(".metadata.txt")
                outmeta.write_text(metadata)
                output_files.append(outmeta)

            if len(output_netcdfs) == 1:
                output_final = output_netcdfs[0].with_suffix(".zip")
            else:
                output_final = Path(self.workdir) / f"{self.identifier}_output.zip"
            zip_files(output_final, output_files)
        else:
            output_final = output_files[0]

        metalink = make_metalink_output(self, output_files)

        response.outputs["output"].file = str(output_final)
        response.outputs["output_log"].file = str(log_file_path(self))
        response.outputs["ref"].data = metalink.xml

        write_log(self, "Processing finished successfully", process_step="done")

        return response


def _make_unique_drs_filename(
    ds: xr.Dataset, existing_names: List[str], output_name: Optional[str] = None
):
    """Generate a drs filename: avoid overwriting files by adding a dash and a number to the filename."""
    if output_name is not None:
        filename = f"{output_name}.nc"
    else:
        try:
            filename = drs_filename(ds)
        except KeyError:
            filename = "out.nc"

    count = 0
    new_filename = valid_filename(filename)
    while new_filename in existing_names:
        count += 1
        new_filename = f"{filename.replace('.nc', '')}-{count}.nc"
    return new_filename
