import logging
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Callable, Deque, Dict, Generator, Iterable, List, Tuple, Union
import zipfile

import netCDF4
import numpy as np
import pandas as pd
from pywps import FORMATS, Process, configuration
from pywps import (
    BoundingBoxInput,
    BoundingBoxOutput,
    ComplexInput,
    ComplexOutput,
    LiteralInput,
    LiteralOutput,
)
from pywps.inout.outputs import MetaFile, MetaLink4
import requests
from requests.exceptions import ConnectionError, InvalidSchema, MissingSchema
import sentry_sdk
import xarray as xr

LOGGER = logging.getLogger("PYWPS")

PywpsInput = Union[LiteralInput, ComplexInput, BoundingBoxInput]
PywpsOutput = Union[LiteralOutput, ComplexOutput, BoundingBoxOutput]
RequestInputs = Dict[str, Deque[PywpsInput]]


def log_file_path(process: Process) -> Path:
    """Returns the filepath to write the process logfile."""
    return Path(process.workdir) / "log.txt"


def write_log(
    process: Process,
    message: str,
    level=logging.INFO,
    *,
    process_step: str = None,
    subtask_percentage: int = None,
):
    """Log the process status.

     - With the logging module
     - To a log file stored in the process working directory
     - Update the response document with the message and the status percentage

    subtask_percentage: not the percentage of the whole process, but the percent done
    in the current processing step. (see `process.status_percentage_steps`)
    """
    LOGGER.log(level, message)

    status_percentage = process.response.status_percentage

    # if a process_step is given, set this as the status percentage
    if process_step:
        status_percentage = process.status_percentage_steps.get(
            process_step, status_percentage
        )

    # if a subtask percentage is given, add this value to the status_percentage
    if subtask_percentage is not None:
        steps_percentages = list(process.status_percentage_steps.values())
        for n, percent in enumerate(steps_percentages):
            if status_percentage < percent:
                next_step_percentage = percent
                current_step_percentage = steps_percentages[n - 1]
                break
        else:
            current_step_percentage, next_step_percentage = 1, 100
            if steps_percentages:
                current_step_percentage = steps_percentages[-1]
        step_delta = next_step_percentage - current_step_percentage
        sub_percentage = subtask_percentage / 100 * step_delta
        status_percentage = current_step_percentage + int(sub_percentage)

    if level >= logging.INFO:
        log_file_path(process).open("a", encoding="utf8").write(message + "\n")
        try:
            process.response.update_status(message, status_percentage=status_percentage)
        except AttributeError:
            pass


def compute_indices(
    process: Process, func: Callable, inputs: RequestInputs
) -> xr.Dataset:
    kwds = {}
    global_attributes = None
    for name, input_queue in inputs.items():
        input = input_queue[0]
        if isinstance(input, ComplexInput):
            ds = try_opendap(input)
            global_attributes = global_attributes or ds.attrs
            try:
                kwds[name] = ds.data_vars[name]
            except KeyError as e:
                raise KeyError(
                    f"Variable name '{name}' not in data_vars {list(ds.data_vars)}"
                ) from e
        elif isinstance(input, LiteralInput):
            kwds[name] = input.data

    global_attributes.update(
        {
            "climateindex_package_id": "https://github.com/Ouranosinc/xclim",
            "product": "derived climate index",
            "contact": "Canadian Centre for Climate Services",
            "institution": "Canadian Centre for Climate Services (CCCS)",
            "institute_id": "CCCS",
        }
    )

    out = func(**kwds)
    output_dataset = xr.Dataset(
        data_vars=None, coords=out.coords, attrs=global_attributes
    )
    output_dataset[out.name] = out
    return output_dataset


def try_opendap(
    input: ComplexInput,
    *,
    chunks=None,
    decode_times=True,
    logging_function=lambda message: None,
) -> xr.Dataset:
    """Try to open the file as an OPeNDAP url and chunk it.

    If OPeNDAP fails, access the file directly.
    """
    url = input.url
    if is_opendap_url(url):
        ds = xr.open_dataset(url, chunks=chunks, decode_times=decode_times)
        if not chunks:
            ds = ds.chunk(chunk_dataset(ds, max_size=1000000))
        logging_function(f"Opened dataset as an OPeNDAP url: {url}")
    else:
        if url.startswith("http"):
            # Accessing the file property writes it to disk if it's a url
            logging_function(f"Downloading dataset for url: {url}")
        else:
            logging_function(f"Opening as local file: {input.file}")
        ds = xr.open_dataset(input.file, decode_times=decode_times)

    return ds


def process_threaded(function: Callable, inputs: Iterable):
    """Based on the current configuration, process a list threaded or not."""

    threads = int(configuration.get_config_value("finch", "subset_threads"))
    if threads > 1:
        pool = ThreadPool(processes=threads)
        outputs = list(pool.imap_unordered(function, inputs))
        pool.close()
        pool.join()
    else:
        outputs = [function(r) for r in inputs]

    return outputs


def chunk_dataset(ds, max_size=1000000):
    """Ensures the chunked size of a xarray.Dataset is below a certain size

    Cycle through the dimensions, divide the chunk size by 2 until criteria is met.
    """
    from functools import reduce
    from operator import mul
    from itertools import cycle

    chunks = dict(ds.sizes)

    def chunk_size():
        return reduce(mul, chunks.values())

    for dim in cycle(chunks):
        if chunk_size() < max_size:
            break
        chunks[dim] = max(chunks[dim] // 2, 1)

    return chunks


def make_metalink_output(
    process: Process, files: List[Path], description: str = None
) -> MetaLink4:
    """Make a metalink output from a list of files"""

    metalink = MetaLink4(
        identity=process.identifier,
        description=description,
        publisher="Finch",
        workdir=process.workdir,
    )

    for f in files:
        mf = MetaFile(identity=f.stem, fmt=FORMATS.NETCDF)
        mf.file = str(f)
        metalink.append(mf)

    return metalink


def is_opendap_url(url):
    """
    Check if a provided url is an OpenDAP url.

    The DAP Standard specifies that a specific tag must be included in the
    Content-Description header of every request. This tag is one of:
        "dods-dds" | "dods-das" | "dods-data" | "dods-error"

    So we can check if the header starts with `dods`.

    Even then, some OpenDAP servers seem to not include the specified header...
    So we need to let the netCDF4 library actually open the file.
    """
    try:
        content_description = requests.head(url, timeout=5).headers.get(
            "Content-Description"
        )
    except (ConnectionError, MissingSchema, InvalidSchema):
        return False

    if content_description:
        return content_description.lower().startswith("dods")
    else:
        try:
            dataset = netCDF4.Dataset(url)
        except OSError:
            return False
        return dataset.disk_format in ("DAP2", "DAP4")


def single_input_or_none(inputs, identifier):
    try:
        return inputs[identifier][0].data
    except KeyError:
        return None


def netcdf_file_list_to_csv(
    netcdf_files: Union[List[Path], List[str]], output_folder, filename_prefix
) -> Tuple[List[str], str]:
    """Write csv files for a list of netcdf files.

    Produces one csv file per calendar type, along with a metadata folder in
    the output_folder."""
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    def get_attrs_fallback(ds, *args):
        for key in args:
            try:
                return ds.attrs[key]
            except KeyError:
                continue
        raise KeyError(f"Couldn't find any attribute in [{', '.join(args)}]")

    metadata = {}
    concat_by_calendar = {}
    for file in netcdf_files:
        ds = xr.open_dataset(str(file), decode_times=False)
        calendar = ds.time.calendar
        ds["time"] = xr.decode_cf(ds).time

        for variable in ds.data_vars:
            # for a specific dataset the keys are different:
            # BCCAQv2+ANUSPLIN300_BNU-ESM_historical+rcp85_r1i1p1_19500101-21001231
            model = get_attrs_fallback(ds, "driving_model_id", "GCM__model_id")
            experiment = get_attrs_fallback(
                ds, "driving_experiment_id", "GCM__experiment"
            )
            experiment = experiment.replace(",", "_")

            output_variable = f"{variable}_{model}_{experiment}"

            units = ds[variable].units
            if units:
                output_variable += f"_({units})"

            ds = ds.rename({variable: output_variable})

            df = dataset_to_dataframe(ds)

            if calendar not in concat_by_calendar:
                if "lat" in df.index.names and "lon" in df.index.names:
                    df = df.reset_index(["lat", "lon"])
                concat_by_calendar[calendar] = [df]
            else:
                concat_by_calendar[calendar].append(df[output_variable])

            metadata[output_variable] = format_metadata(ds)

    output_csv_list = []
    for calendar_type, data in concat_by_calendar.items():
        output_csv = output_folder / f"{filename_prefix}_{calendar_type}.csv"
        concat = pd.concat(data, axis=1)

        try:
            concat = concat.reset_index().set_index("time").drop(columns="region")
        except KeyError:
            pass

        dropna_threshold = 3  # lat + lon + at least one value
        concat.dropna(thresh=dropna_threshold, inplace=True)

        concat.to_csv(output_csv)
        output_csv_list.append(output_csv)

    metadata_folder = output_folder / "metadata"
    metadata_folder.mkdir(parents=True, exist_ok=True)
    for output_variable, info in metadata.items():
        metadata_file = metadata_folder / f"{output_variable}.csv"
        metadata_file.write_text(info)

    return output_csv_list, str(metadata_folder)


def dataset_to_dataframe(ds: xr.Dataset) -> pd.DataFrame:
    """Convert a Dataset, while keeping the hour of the day uniform at hour=12"""
    if not np.all(ds.time.dt.hour == 12):
        attrs = ds.time.attrs

        # np.datetime64 doesn't have the 'replace' method
        time_values = ds.time.values
        if not hasattr(time_values[0], "replace"):
            time_values = pd.to_datetime(time_values)

        ds["time"] = [y.replace(hour=12) for y in time_values]
        ds.time.attrs = attrs

    return ds.to_dataframe()


def format_metadata(ds) -> str:
    """For an xarray dataset, return its formatted metadata."""

    def _fmt_attrs(obj, name="", comment="# ", tab=" "):
        """Return string of an object's attribute."""
        lines = ["", name]
        for key, val in obj.attrs.items():
            lines.append(
                tab + key + ":: " + str(val).replace("\n", "\n" + comment + tab + "  ")
            )

        out = ("\n" + comment + tab).join(lines)
        return out

    objs = [
        ({"": ds}, "Global attributes"),
        (ds.coords, "Coordinates"),
        (ds.data_vars, "Data variables"),
    ]

    out = ""
    for obj, name in objs:
        out += "# " + name
        tab = "" if name == "Global attributes" else "  "
        for key, val in obj.items():
            out += _fmt_attrs(val, key, tab=tab)
        out += "\n#\n"
    return out


def zip_files(
    output_filename, files: Iterable, log_function: Callable[[str, int], None] = None
):
    """Create a zipfile from a list of files or folders.

    log_function is a function that receives a message and a percentage."""
    log_function = log_function or (lambda *a: None)
    with zipfile.ZipFile(
        output_filename, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as z:
        all_files = []
        for file in files:
            file = Path(file)
            if file.is_dir():
                all_files += list(file.rglob("*.*"))
            else:
                all_files.append(file)

        common_folder = None
        all_parents = [list(reversed(file.parents)) for file in all_files]
        for parents in zip(*all_parents):
            if len(set(parents)) == 1:
                common_folder = parents[0]
            else:
                break

        n_files = len(all_files)
        for n, filename in enumerate(all_files):

            percentage = int(n / n_files * 100)
            message = f"Zipping file {n + 1} of {n_files}"
            log_function(message, percentage)

            arcname = filename.relative_to(common_folder) if common_folder else None
            z.write(filename, arcname=arcname)


def make_tasmin_tasmax_pairs(
    filenames: List[Path],
) -> Generator[Tuple[Path, Path], None, None]:
    """Returns pairs of corresponding tasmin-tasmax files based on their filename"""

    tasmin_files = [f for f in filenames if "tasmin" in f.name.lower()]
    tasmax_files = [f for f in filenames if "tasmax" in f.name.lower()]
    for tasmin in tasmin_files[:]:
        for tasmax in tasmax_files[:]:
            if tasmin.name.lower() == tasmax.name.lower().replace("tasmax", "tasmin"):
                yield tasmin, tasmax
                tasmax_files.remove(tasmax)
                tasmin_files.remove(tasmin)
                break
    for f in tasmax_files + tasmax_files:
        sentry_sdk.capture_message(
            f"Couldn't find matching tasmin or tasmax for: {f}", level="error"
        )
