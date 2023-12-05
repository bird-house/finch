# noqa: D100
import json
import logging
import os
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import chain
from multiprocessing.pool import ThreadPool
from pathlib import Path
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

import cftime
import numpy as np
import pandas as pd
import requests
import sentry_sdk
import xarray as xr
import xclim
import yaml
from netCDF4 import num2date
from pandas.api.types import is_numeric_dtype
from pywps import (
    FORMATS,
    BoundingBoxInput,
    BoundingBoxOutput,
    ComplexInput,
    ComplexOutput,
    LiteralInput,
    LiteralOutput,
    Process,
    configuration,
)
from pywps.configuration import get_config_value
from pywps.inout.outputs import MetaFile, MetaLink4
from requests.exceptions import ConnectionError, InvalidSchema, MissingSchema
from slugify import slugify
from xclim.core.indicator import build_indicator_module_from_yaml
from xclim.core.utils import InputKind

LOGGER = logging.getLogger("PYWPS")

PywpsInput = Union[LiteralInput, ComplexInput, BoundingBoxInput]
PywpsOutput = Union[LiteralOutput, ComplexOutput, BoundingBoxOutput]
RequestInputs = Dict[str, Deque[PywpsInput]]

# These are parameters that set options. They are not `compute` arguments.
INDICATOR_OPTIONS = [
    "check_missing",
    "missing_options",
    "cf_compliance",
    "data_validation",
]


def get_virtual_modules():
    """Load virtual modules."""
    modules = {}
    if modfiles := get_config_value("finch", "xclim_modules"):
        for modfile in modfiles.split(","):
            if os.path.isabs(modfile):
                mod = build_indicator_module_from_yaml(Path(modfile))
            else:
                mod = build_indicator_module_from_yaml(
                    Path(__file__).parent.parent.joinpath(modfile)
                )
            indicators = []
            for indname, ind in mod.iter_indicators():
                indicators.append(ind.get_instance())
            modules[Path(modfile).name] = dict(indicators=indicators)
    return modules


@dataclass
class DatasetConfiguration:
    """Dataset Configuration class.

    Attributes
    ----------
    path: str
        The path (or url) to the root directory where to search for the data.
    pattern: str
        The pattern of the filenames. Must include at least : "variable", "scenario" and "model".
        Patterns must be understandable by :py:func:`parse.parse`.
    local: bool
        Whether the path points to a local directory or a remote THREDDS catalog.
    depth : int
        The depth to which search for files below the directory. < 0 will search recursively.
    suffix : str
        When the files are local, this is the suffix of the files.
    allowed_values : dict
        Mapping from field name to a list of allowed values.
        Must include "scenario", "model" and "variable",
        the latter defines which variable are available and thus which indicator can be used.
    model_lists : dict
        A mapping from list name to a list of model names to provide special sub-lists.
        The values can also be a tuple of (model name, realization numer),
        in which case, pattern must include a "realization" field.
    """

    path: str
    pattern: str
    local: bool
    allowed_values: dict
    depth: int = 0
    suffix: str = "*nc"
    model_lists: dict = field(default_factory=dict)


def get_datasets_config():  # noqa: D103
    p = get_config_value("finch", "datasets_config")
    if not p:  # No config given.
        return {}

    if not Path(p).is_absolute():
        p = Path(__file__).parent.parent / p

    with open(p) as f:
        conf = yaml.safe_load(f)
    return {ds: DatasetConfiguration(**dsconf) for ds, dsconf in conf.items()}


def get_available_variables():  # noqa: D103
    conf = get_datasets_config()
    return set(chain(*(d.allowed_values["variable"] for d in conf.values())))


def iter_xc_variables(indicator: xclim.core.indicator.Indicator):  # noqa: D103
    for n, p in indicator.parameters.items():
        if p.kind in [InputKind.VARIABLE, InputKind.OPTIONAL_VARIABLE]:
            yield n


def log_file_path(process: Process) -> Path:
    """Return the filepath to write the process logfile."""
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
    """Get all explicitly passed metadata attributes from the config in section finch:metadata."""
    # Remove all "defaults", only keep explicitly-passed options
    # This works because we didn't define any defaults for this section.
    # But will do strange things if any of the defaults have the same name as a passed field
    # This is especially risky, since ALL environment variables are listed in the defaults...
    names = set(configuration.CONFIG["finch:metadata"].keys()) - set(
        configuration.CONFIG._defaults.keys()
    )

    return {
        name: configuration.get_config_value("finch:metadata", name) for name in names
    }


def compute_indices(
    process: Process, func: Callable, inputs: RequestInputs
) -> xr.Dataset:  # noqa: D103
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
                ds = try_opendap(
                    input, logging_function=lambda msg: write_log(process, msg)
                )
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
        **user_attrs,
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
    """Generate filename according to the data reference syntax (DRS).

    Parameters
    ----------
    ds : xr.Dataset
    variable : str
        appropriate variable for filename, if not set (default), variable will be determined from the dataset variables.

    Returns
    -------
    str
        DRS filename

    Raises
    ------
    KeyError
        When the dataset doesn't have the required attributes.

    Notes
    -----
    Copied and modified from https://github.com/bird-house/eggshell which doesn't have a release usable by finch.

    Based on the metadata in the resource.
    http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
    https://pypi.python.org/pypi/drslib
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
    chunks="auto",
    decode_times=True,
    chunk_dims=None,
    logging_function=lambda message: None,
) -> xr.Dataset:
    """Try to open the file as an OPeNDAP url and chunk it.

    By default, chunks are to be determined by xarray/dask.
    If `chunks=None` or `chunks_dims` is given, finch rechunks the dataset according to
    the logic of `chunk_dataset`.
    Pass `chunks=False` to disable dask entirely on this dataset.
    """
    url = input.url
    logging_function(f"Try opening DAP link {url}")

    if is_opendap_url(url):
        path = url
        logging_function(f"Opened dataset as an OPeNDAP url: {url}")
    else:
        if url.startswith("http"):
            # Accessing the file property writes it to disk if it's a url
            logging_function(f"Downloading dataset for url: {url}")
        else:
            logging_function(f"Opening as local file: {input.file}")
        path = input.file

    try:
        # Try to open the dataset
        ds = xr.open_dataset(path, chunks=chunks or None, decode_times=decode_times)
    except NotImplementedError:
        if chunks == "auto":
            # Some dtypes are not compatible with auto chunking (object, so unbounded strings)
            logging_function(
                "xarray auto-chunking failed, opening with no chunks and inferring chunks ourselves."
            )
            chunks = None
            ds = xr.open_dataset(path, chunks=None, decode_times=decode_times)
        else:
            raise

    # To handle large number of grid cells (50+) in subsetted data
    if "region" in ds.dims and "time" in ds.dims:
        chunks = dict(time=-1, region=5)
        ds = ds.chunk(chunks)
    elif chunks is None or chunk_dims is not None:
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
    """Ensure the chunked size of a xarray.Dataset is below a certain size.

    Cycle through the dimensions, divide the chunk size by 2 until criteria is met.
    If chunk_dims is given, limits the chunking to those dimensions, if they are
    found in the dataset.
    """
    from functools import reduce
    from itertools import cycle
    from operator import mul

    chunks = dict(ds.sizes)

    dims = set(ds.dims).intersection(chunk_dims or ds.dims)
    if not dims:
        LOGGER.warning(
            f"Provided dimension names for chunking ({chunk_dims}) were "
            f"not found in dataset dims ({ds.dims}). No chunking was done."
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
    """Make a MetaLink output from a list of files."""
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
    """Check if a provided url is an OpenDAP url.

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

        # try:
        #     # For a non-DAP URL, this just hangs python.
        #     dataset = netCDF4.Dataset(url)
        # except OSError:
        #     return False
        # return dataset.disk_format in ("DAP2", "DAP4")


def single_input_or_none(inputs, identifier) -> Optional[str]:
    """Return first input item."""
    try:
        return inputs[identifier][0].data
    except KeyError:
        return None


def netcdf_file_list_to_csv(
    netcdf_files: Union[List[Path], List[str]],
    output_folder,
    filename_prefix,
    csv_precision: Optional[int] = None,
) -> Tuple[List[str], str]:
    """Write csv files for a list of netcdf files.

    Produces one csv file per calendar type, along with a metadata folder in the output_folder.
    """
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
        coords = ds.coords
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
            if csv_precision and csv_precision < 0:
                ds = ds.round(csv_precision)
                csv_precision = 0
            df = dataset_to_dataframe(ds)

            if calendar not in concat_by_calendar:
                # TODO: Why was this there? When we have a time axis, this makes the concat fail.
                # if "lat" in df.index.names and "lon" in df.index.names:
                #     df = df.reset_index(["lat", "lon"])
                concat_by_calendar[calendar] = [df]
            else:
                concat_by_calendar[calendar].append(df[output_variable])

            metadata[output_variable] = format_metadata(ds)

    output_csv_list = []
    for calendar_type, data in concat_by_calendar.items():
        output_csv = output_folder / f"{filename_prefix}_{calendar_type}.csv"
        concat = pd.concat(data, axis=1)

        if "region" in concat.reset_index().columns:
            concat = (
                concat.reset_index()
                .sort_values(["region", "time"])
                .set_index(["lat", "lon", "time"])
                .drop(columns="region")
            )
        else:
            concat = (
                concat.reset_index()
                .sort_values(["lat", "lon", "time"])
                .set_index(["lat", "lon", "time"])
            )

        dropna_threshold = 1  # at least one value
        concat.dropna(thresh=dropna_threshold, inplace=True)
        if csv_precision is not None:
            for v in concat:
                if v not in coords and is_numeric_dtype(concat[v]):
                    concat[v] = concat[v].map(
                        lambda x: f"{x:.{csv_precision}f}" if not pd.isna(x) else ""
                    )
        concat.to_csv(output_csv)
        output_csv_list.append(output_csv)

    metadata_folder = output_folder / "metadata"
    metadata_folder.mkdir(parents=True, exist_ok=True)
    for output_variable, info in metadata.items():
        metadata_file = metadata_folder / f"{output_variable}.csv"
        metadata_file.write_text(info)

    return output_csv_list, str(metadata_folder)


def dataset_to_dataframe(ds: xr.Dataset) -> pd.DataFrame:
    """Convert a Dataset while keeping the hour of the day uniform at hour=12."""
    if not np.all(ds.time.dt.hour == 12):
        attrs = ds.time.attrs

        # np.datetime64 doesn't have the 'replace' method
        time_values = ds.time.values
        if not hasattr(time_values[0], "replace"):
            time_values = pd.to_datetime(time_values)

        ds["time"] = [y.replace(hour=12) for y in time_values]
        ds.time.attrs = attrs
    df = ds.to_dataframe().reset_index()

    if "realization" not in ds.dims:
        new_cols = [ll for ll in ["lat", "lon", "time"] if ll in df.columns]
    else:
        new_cols = [
            ll
            for ll in ["lat", "lon", "time", "scenario", "region"]
            if ll in df.columns
        ]
        values = [c for c in df.columns if c not in new_cols and c != "realization"]
        df = df.pivot(
            index=new_cols,
            columns="realization",
            values=values,
        ).reset_index()
        # pivot table columns are multi-indexes : flatten
        df.columns = [":".join(d) if d[1] else d[0] for d in df.columns]

    df = df.sort_values(new_cols).set_index(new_cols)

    # new_cols.extend([ll for ll in df.columns if ll not in new_cols])
    return df


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

    log_function is a function that receives a message and a percentage.
    """
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
    """Return pairs of corresponding tasmin-tasmax files based on their filename."""
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
    """Fix for a single broken index in a specific file."""
    if "time" not in ds.dims:
        return

    time_dim = ds.time.values
    times_are_encoded = "units" in ds.time.attrs

    if times_are_encoded:
        wrong_id = np.argwhere(np.isclose(time_dim, 0))
    else:
        if ds.time.dt.calendar != "noleap":
            return
        wrong_id = np.argwhere(
            time_dim == cftime.DatetimeNoLeap(year=1850, month=1, day=1, hour=0)
        )

    if wrong_id.size == 0:
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
    """Write an :py:class:`xarray.Dataset` dataset to disk, optionally using compression."""
    encoding = {}

    if "time" in ds.dims:
        encoding["time"] = {
            "dtype": "single",  # better compatibility with OpenDAP in thredds
        }
        fix_broken_time_index(ds)
    if compression_level:
        for v in ds.data_vars:
            encoding[v] = {"zlib": True, "complevel": compression_level}

    # Perform computations
    ds.load()

    # This is necessary when running with gunicorn to avoid lock-ups
    ds.to_netcdf(str(output_path), format="NETCDF4", encoding=encoding)


def update_history(
    hist_str: str,
    *inputs_list: Union[xr.DataArray, xr.Dataset],
    new_name: Optional[str] = None,
    **inputs_kws: Union[xr.DataArray, xr.Dataset],
):
    r"""Return a history string with the timestamped message and the combination of the history of all inputs.

    The new history entry is formatted as "[<timestamp>] <new_name>: <hist_str> - finch version : <finch version>."

    Parameters
    ----------
    hist_str : str
      The string describing what has been done on the data.
    new_name : Optional[str]
      The name of the newly created variable or dataset to prefix hist_msg.
    \*inputs_list : Union[xr.DataArray, xr.Dataset]
      The datasets or variables that were used to produce the new object.
      Inputs given that way will be prefixed by their "name" attribute if available.
    **inputs_kws : Union[xr.DataArray, xr.Dataset]
      Mapping from names to the datasets or variables that were used to produce the new object.
      Inputs given that way will be prefixes by the passed name.

    Returns
    -------
    str
      The combine history of all inputs starting with `hist_str`.

    See Also
    --------
    merge_attributes
    """
    from finch import __version__  # pylint: disable=cyclic-import

    merged_history = xclim.core.formatting.merge_attributes(
        "history",
        *inputs_list,
        new_line="\n",
        missing_str="",
        **inputs_kws,
    )
    if len(merged_history) > 0 and not merged_history.endswith("\n"):
        merged_history += "\n"
    merged_history += (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {new_name or ''}: "
        f"{hist_str} - finch version: {__version__}."
    )
    return merged_history


def valid_filename(name: Union[Path, str]) -> Union[Path, str]:
    """Remove unsupported characters from a filename.

    Returns
    -------
    str or Path

    Examples
    --------
    >>> valid_filename("summer's tasmin.nc")
    'summers_tasmin.nc'
    """
    p = Path(name)
    s = slugify(p.stem, separator="_")
    if not s:
        raise ValueError(f"Filename not valid. Got {name}.")
    out = p.parent / (s + p.suffix)
    if isinstance(name, str):
        return str(out)
    return out
