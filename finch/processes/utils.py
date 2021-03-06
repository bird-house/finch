from datetime import timedelta
import logging
from multiprocessing.pool import ThreadPool
from pathlib import Path
import re
import json
from typing import (
    Callable,
    Deque,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)
import zipfile

import cftime
import netCDF4
import numpy as np
import pandas as pd
from pywps import (
    BoundingBoxInput,
    BoundingBoxOutput,
    ComplexInput,
    ComplexOutput,
    FORMATS,
    LiteralInput,
    LiteralOutput,
    Process,
    configuration
)
from pywps.inout.outputs import MetaFile, MetaLink4
import requests
from requests.exceptions import ConnectionError, InvalidSchema, MissingSchema
import sentry_sdk
import xarray as xr
from netCDF4 import num2date
import xclim

LOGGER = logging.getLogger("PYWPS")

PywpsInput = Union[LiteralInput, ComplexInput, BoundingBoxInput]
PywpsOutput = Union[LiteralOutput, ComplexOutput, BoundingBoxOutput]
RequestInputs = Dict[str, Deque[PywpsInput]]

# These are parameters that set options. They are not `compute` arguments.
INDICATOR_OPTIONS = ['check_missing', 'missing_options', "cf_compliance", "data_validation"]


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


def get_attributes_from_config():
    """Get all explicitly passed metadata attributes from the config, in section finch:metadata."""
    # Remove all "defaults", only keep explicitly-passed options
    # This works because we didn't define any defaults for this section.
    # But will do strange things if any of the defaults have the same name as a passed field
    # This is especially risky, since ALL environment variables are listed in the defaults...
    names = (
        set(configuration.CONFIG['finch:metadata'].keys())
        - set(configuration.CONFIG._defaults.keys())
    )

    return {
        name: configuration.get_config_value("finch:metadata", name) for name in names
    }


def compute_indices(
    process: Process, func: Callable, inputs: RequestInputs
) -> xr.Dataset:
    kwds = {}
    global_attributes = {}
    for name, input_queue in inputs.items():
        if isinstance(input_queue[0], LiteralInput):
            value = [inp.data for inp in input_queue]
            if len(input_queue) == 1:
                value = value[0]
            kwds[name] = value

    variable = kwds.pop("variable", None)

    for name, input_queue in inputs.items():
        input = input_queue[0]

        if isinstance(input, ComplexInput):

            if input.supported_formats[0] == FORMATS.JSON:
                kwds[name] = json.loads(input.data)

            elif input.supported_formats[0] in [FORMATS.NETCDF, FORMATS.DODS]:
                ds = try_opendap(input, logging_function=lambda msg: write_log(process, msg))
                global_attributes = global_attributes or ds.attrs
                vars = list(ds.data_vars.values())

                if variable:
                    if variable in ds.data_vars:
                        kwds[name] = ds.data_vars[variable]

                    else:
                        raise KeyError(
                            f"Variable name '{name}' not in data_vars {list(ds.data_vars)}"
                        )
                else:
                    # Get variable matching input parameter name.
                    if name in ds.data_vars:
                        kwds[name] = ds.data_vars[name]

                    # If only one variable in dataset, use it.
                    elif len(vars) == 1:
                        kwds[name] = vars[0]

    user_attrs = get_attributes_from_config()

    global_attributes.update(
        {
            "climateindex_package_id": "https://github.com/Ouranosinc/xclim",
            "product": "derived climate index",
        },
        **user_attrs
    )

    options = {name: kwds.pop(name) for name in INDICATOR_OPTIONS if name in kwds}
    with xclim.core.options.set_options(**options):
        out = func(**kwds)

    output_dataset = xr.Dataset(
        data_vars=None, coords=out.coords, attrs=global_attributes
    )

    # fix frequency of computed output (xclim should handle this)
    if output_dataset.attrs.get("frequency") == "day" and "freq" in kwds:
        conversions = {
            "YS": "yr",
            "MS": "mon",
            "QS-DEC": "seasonal",
            "AS-JUL": "seasonal",
        }
        output_dataset.attrs["frequency"] = conversions.get(kwds["freq"], "day")

    output_dataset[out.name] = out
    return output_dataset


def drs_filename(ds: xr.Dataset, variable: str = None):
    """Copied and modified from https://github.com/bird-house/eggshell
    which doesn't have a release usable by finch.

    generates filename according to the data reference syntax (DRS)
    based on the metadata in the resource.
    http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
    https://pypi.python.org/pypi/drslib
    :param variable: appropriate variable for filename, if not set (default), variable will
                      be determined from the dataset variables.
    :return str: DRS filename
    :raises KeyError: When the dataset doesn't have the required attributes.
    """
    if len(ds.data_vars) == 1:
        variable = list(ds.data_vars)[0]

    if variable is None:
        variable = [k for k, v in ds.variables.items() if len(v.dims) >= 3][0]
    variable = variable.replace("_", "-")

    # CORDEX example: tas_EUR-11_ICHEC-EC-EARTH_historical_r3i1p1_DMI-HIRHAM5_v1_day
    cordex_pattern = "{variable}_{domain}_{driving_model}_{experiment}_{ensemble}_{model}_{version}_{frequency}"

    # CMIP5 example: tas_MPI-ESM-LR_historical_r1i1p1
    cmip5_pattern = "{variable}_{model}_{experiment}_{ensemble}"

    if ds.attrs["project_id"] in ("CORDEX", "EOBS"):
        filename = cordex_pattern.format(
            variable=variable,
            domain=ds.attrs["CORDEX_domain"],
            driving_model=ds.attrs["driving_model_id"],
            experiment=ds.attrs["experiment_id"],
            ensemble=ds.attrs["driving_model_ensemble_member"],
            model=ds.attrs["model_id"],
            version=ds.attrs["rcm_version_id"],
            frequency=ds.attrs["frequency"],
        )
    elif ds.attrs["project_id"] == "CMIP5":
        ensemble = "r{}i{}p{}".format(
            ds.attrs["driving_realization"],
            ds.attrs["driving_initialization_method"],
            ds.attrs["driving_physics_version"],
        )
        filename = cmip5_pattern.format(
            variable=variable,
            model=ds.attrs["driving_model_id"],
            experiment=ds.attrs["driving_experiment_id"].replace(",", "+"),
            ensemble=ensemble,
        )
    else:
        params = [
            variable,
            ds.attrs.get("frequency"),
            ds.attrs.get("model_id"),
            ds.attrs.get("driving_model_id"),
            ds.attrs.get("experiment_id", "").replace(",", "+"),
            ds.attrs.get("driving_experiment_id", "").replace(",", "+"),
        ]
        params = [k for k in params if k]
        filename = "_".join(params)

    if "time" in ds:
        date_from = ds.time[0].values
        date_to = ds.time[-1].values

        if "units" in ds.time.attrs:
            # times are encoded
            units = ds.time.units
            calendar = ds.time.attrs.get("calendar", "standard")
            date_from = num2date(date_from, units, calendar)
            date_to = num2date(date_to, units, calendar)

        date_from = pd.to_datetime(str(date_from))
        date_to = pd.to_datetime(str(date_to))

        filename += f"_{date_from:%Y%m%d}-{date_to:%Y%m%d}"

    # sanitize any spaces that came from the source input's metadata
    filename = filename.replace(" ", "-")

    filename += ".nc"

    return filename


def try_opendap(
    input: ComplexInput,
    *,
    chunks=None,
    decode_times=True,
    chunk_dims=None,
    logging_function=lambda message: None,
) -> xr.Dataset:
    """Try to open the file as an OPeNDAP url and chunk it.

    If OPeNDAP fails, access the file directly.
    """
    url = input.url
    logging_function(f"Try opening DAP link {url}")

    if is_opendap_url(url):
        ds = xr.open_dataset(url, chunks=chunks, decode_times=decode_times)
        logging_function(f"Opened dataset as an OPeNDAP url: {url}")
    else:
        if url.startswith("http"):
            # Accessing the file property writes it to disk if it's a url
            logging_function(f"Downloading dataset for url: {url}")
        else:
            logging_function(f"Opening as local file: {input.file}")

        ds = xr.open_dataset(input.file, chunks=chunks, decode_times=decode_times)

        # To handle large number of grid cells (50+) in subsetted data
        if "region" in ds.dims and "time" in ds.dims:
            chunks = dict(time=-1, region=5)
            ds = ds.chunk(chunks)
    if not chunks:
        ds = ds.chunk(chunk_dataset(ds, max_size=1000000, chunk_dims=chunk_dims))
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


def chunk_dataset(ds, max_size=1000000, chunk_dims=None):
    """Ensures the chunked size of a xarray.Dataset is below a certain size.

    Cycle through the dimensions, divide the chunk size by 2 until criteria is met.
    If chunk_dims is given, limits the chunking to those dimensions, if they are
    found in the dataset.
    """
    from functools import reduce
    from operator import mul
    from itertools import cycle

    chunks = dict(ds.sizes)

    dims = set(ds.dims).intersection(chunk_dims or ds.dims)
    if not dims:
        LOGGER.warning(
            (f"Provided dimension names for chunking ({chunk_dims}) were "
             f"not found in dataset dims ({ds.dims}). No chunking was done.")
        )
        return chunks

    def chunk_size():
        return reduce(mul, chunks.values())

    for dim in cycle(dims):
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
        return False

        try:
            # For a non-DAP URL, this just hangs python.
            dataset = netCDF4.Dataset(url)
        except OSError:
            return False
        return dataset.disk_format in ("DAP2", "DAP4")


def single_input_or_none(inputs, identifier) -> Optional[str]:
    """Return first input item."""
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


def fix_broken_time_index(ds: xr.Dataset):
    """Fix for a single broken index in a specific file"""
    if "time" not in ds.dims:
        return

    time_dim = ds.time.values
    times_are_encoded = "units" in ds.time.attrs

    if times_are_encoded:
        wrong_id = np.argwhere(np.isclose(time_dim, 0))
    else:
        wrong_id = np.argwhere(
            time_dim == cftime.DatetimeNoLeap(year=1850, month=1, day=1, hour=0)
        )

    if not wrong_id:
        return
    wrong_id = wrong_id[0, 0]
    if wrong_id == 0 or wrong_id == len(ds.time) - 1:
        return

    daily_gap = 1.0 if times_are_encoded else timedelta(days=1)

    is_daily = time_dim[wrong_id + 1] - time_dim[wrong_id - 1] == daily_gap * 2

    if is_daily:
        fixed_time = time_dim
        fixed_time[wrong_id] = time_dim[wrong_id - 1] + daily_gap
        attrs = ds.time.attrs
        ds["time"] = fixed_time
        ds.time.attrs = attrs


def dataset_to_netcdf(
    ds: xr.Dataset, output_path: Union[Path, str], compression_level=0
) -> None:
    """Write an :class:`xarray.Dataset` dataset to disk, optionally using compression."""
    encoding = {}

    if "time" in ds.dims:
        encoding["time"] = {
            "dtype": "single",  # better compatibility with OpenDAP in thredds
        }
        fix_broken_time_index(ds)
    if compression_level:
        for v in ds.data_vars:
            encoding[v] = {"zlib": True, "complevel": compression_level}

    ds.to_netcdf(str(output_path), format="NETCDF4", encoding=encoding)
