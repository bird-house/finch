from collections import deque
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

from pywps import ComplexInput, FORMATS, Process
from pywps import configuration
from pywps.app.exceptions import ProcessError
from siphon.catalog import TDSCatalog
import xarray as xr
from xclim import ensembles
from xclim.checks import assert_daily
from xclim.utils import Indicator

from . import wpsio
from .utils import (
    PywpsInput,
    RequestInputs,
    compute_indices,
    dataset_to_dataframe,
    format_metadata,
    single_input_or_none,
    write_log,
    zip_files,
)
from .wps_xclim_indices import make_nc_input


xclim_netcdf_variables = {
    "tasmin",
    "tasmax",
    "tas",
    "pr",
    "prsn",
    "tn10",
    "tn90",
    "t10",
    "t90",
}  # a list of all posible netcdf arguments in xclim

bccaq_variable_types = {"tasmin", "tasmax", "pr"}


class ParsingMethod(Enum):
    # parse the filename directly (faster and simpler, more likely to fail)
    filename = 1
    # parse each Data Attribute Structure (DAS) by appending .das to the url
    # One request for each dataset, so lots of small requests to the Thredds server
    opendap_das = 2
    # open the dataset using xarray and look at the file attributes
    # safer, but slower and lots of small requests are made to the Thredds server
    xarray = 3


def get_bccaqv2_local_files_datasets(
    catalog_url, variable=None, rcp=None, method: ParsingMethod = ParsingMethod.filename
) -> List[str]:
    """Get a list of filenames corresponding to variable and rcp on a local filesystem."""
    urls = []
    for file in Path(catalog_url).glob("*.nc"):
        if _bccaqv2_filter(method, file.stem, str(file), rcp, variable):
            urls.append(str(file))
    return urls


def get_bccaqv2_opendap_datasets(
    catalog_url, variable=None, rcp=None, method: ParsingMethod = ParsingMethod.filename
) -> List[str]:
    """Get a list of urls corresponding to variable and rcp on a Thredds server.

    We assume that the files are named in a certain way on the Thredds server.

    This is the case for boreas.ouranos.ca/thredds
    For more general use cases, see the `xarray` and `requests` methods below."""

    catalog = TDSCatalog(catalog_url)

    urls = []
    for dataset in catalog.datasets.values():
        opendap_url = dataset.access_urls["OPENDAP"]
        if _bccaqv2_filter(method, dataset.name, opendap_url, rcp, variable):
            urls.append(opendap_url)
    return urls


def _bccaqv2_filter(method: ParsingMethod, filename, url, rcp, variable):
    """Parse metadata and filter BCCAQV2 datasets"""

    variable_ok = variable is None
    rcp_ok = rcp is None

    keep_models = [
        m.lower()
        for m in [
            "BNU-ESM",
            "CCSM4",
            "CESM1-CAM5",
            "CNRM-CM5",
            "CSIRO-Mk3-6-0",
            "CanESM2",
            "FGOALS-g2",
            "GFDL-CM3",
            "GFDL-ESM2G",
            "GFDL-ESM2M",
            "HadGEM2-AO",
            "HadGEM2-ES",
            "IPSL-CM5A-LR",
            "IPSL-CM5A-MR",
            "MIROC-ESM-CHEM",
            "MIROC-ESM",
            "MIROC5",
            "MPI-ESM-LR",
            "MPI-ESM-MR",
            "MRI-CGCM3",
            "NorESM1-M",
            "NorESM1-ME",
            "bcc-csm1-1-m",
            "bcc-csm1-1",
        ]
    ]

    if method == ParsingMethod.filename:
        variable_ok = variable_ok or filename.startswith(variable)
        rcp_ok = rcp_ok or rcp in filename

        filename_lower = filename.lower()
        if not any(m in filename_lower for m in keep_models):
            return False

        if "r1i1p1" not in filename:
            return False

    elif method == ParsingMethod.opendap_das:

        raise NotImplementedError("todo: filter models and runs")

        # re_experiment = re.compile(r'String driving_experiment_id "(.+)"')
        # lines = requests.get(url + ".das").content.decode().split("\n")
        # variable_ok = variable_ok or any(
        #     line.startswith(f"    {variable} {{") for line in lines
        # )
        # if not rcp_ok:
        #     for line in lines:
        #         match = re_experiment.search(line)
        #         if match and rcp in match.group(1).split(","):
        #             rcp_ok = True

    elif method == ParsingMethod.xarray:

        raise NotImplementedError("todo: filter models and runs")

        # import xarray as xr

        # ds = xr.open_dataset(url, decode_times=False)
        # rcps = [
        #     r
        #     for r in ds.attrs.get("driving_experiment_id", "").split(",")
        #     if "rcp" in r
        # ]
        # variable_ok = variable_ok or variable in ds.data_vars
        # rcp_ok = rcp_ok or rcp in rcps

    return rcp_ok and variable_ok


def get_bccaqv2_inputs(
    workdir: str, variable=None, rcp=None, catalog_url=None
) -> List[PywpsInput]:
    """Adds a 'resource' input list with bccaqv2 urls to WPS inputs."""
    catalog_url = configuration.get_config_value("finch", "bccaqv2_url")

    inputs = []

    def _make_bccaqv2_resource_input():
        return ComplexInput(
            "resource",
            "NetCDF resource",
            max_occurs=1000,
            supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
        )

    if catalog_url.startswith("http"):
        for url in get_bccaqv2_opendap_datasets(catalog_url, variable, rcp):
            resource = _make_bccaqv2_resource_input()
            resource.url = url
            resource.workdir = workdir
            inputs.append(resource)
    else:
        for file in get_bccaqv2_local_files_datasets(catalog_url, variable, rcp):
            resource = _make_bccaqv2_resource_input()
            resource.file = file
            resource.workdir = workdir
            inputs.append(resource)

    return inputs


def _formatted_coordinate(value) -> Optional[str]:
    """Returns the first float value.

    The value can be a comma separated list of floats or a single float
    """
    if not value:
        return
    try:
        value = value.split(",")[0]
    except AttributeError:
        pass
    return f"{float(value):.3f}"


def make_output_filename(process: Process, inputs: List[PywpsInput]):
    """Returns a filename for the process's output, depending on its inputs"""

    rcp = single_input_or_none(inputs, "rcp")
    lat = _formatted_coordinate(single_input_or_none(inputs, "lat"))
    lon = _formatted_coordinate(single_input_or_none(inputs, "lon"))
    lat0 = _formatted_coordinate(single_input_or_none(inputs, "lat0"))
    lon0 = _formatted_coordinate(single_input_or_none(inputs, "lon0"))
    lat1 = _formatted_coordinate(single_input_or_none(inputs, "lat1"))
    lon1 = _formatted_coordinate(single_input_or_none(inputs, "lon1"))

    output_parts = [process.identifier]

    if lat and lon:
        output_parts.append(f"{float(lat):.3f}")
        output_parts.append(f"{float(lon):.3f}")
    elif lat0 and lon0:
        output_parts.append(f"{float(lat0):.3f}")
        output_parts.append(f"{float(lon0):.3f}")

    if lat1 and lon1:
        output_parts.append(f"{float(lat1):.3f}")
        output_parts.append(f"{float(lon1):.3f}")

    if rcp:
        output_parts.append(rcp)

    return "_".join(output_parts)


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


def uses_bccaqv2_data(indicator: Indicator) -> bool:
    """Returns True if the BCCAQv2 data can be used directly with this indicator."""

    incompatible_variable_names = xclim_netcdf_variables - bccaq_variable_types

    params = eval(indicator.json()["parameters"])
    return not any(p in incompatible_variable_names for p in params)


def make_indicator_inputs(
    indicator: Indicator, wps_inputs: RequestInputs, files_list: List[Path]
) -> List[RequestInputs]:
    """From a list of files, make a list of inputs used to call the given xclim indicator."""

    arguments = set(eval(indicator.json()["parameters"]))

    required_netcdf_args = bccaq_variable_types.intersection(arguments)

    input_list = []

    if len(required_netcdf_args) == 1:
        variable_name = list(required_netcdf_args)[0]
        for path in files_list:
            inputs = deepcopy(wps_inputs)
            inputs[variable_name] = deque([make_nc_input(variable_name)])
            inputs[variable_name][0].file = str(path)
            input_list.append(inputs)
    else:
        for input_group in make_file_groups(files_list):
            inputs = deepcopy(wps_inputs)
            for variable_name, path in input_group.items():
                if variable_name not in required_netcdf_args:
                    continue
                inputs[variable_name] = deque([make_nc_input(variable_name)])
                inputs[variable_name][0].file = str(path)
            input_list.append(inputs)

    return input_list


def make_file_groups(files_list: List[Path]) -> List[Dict[str, Path]]:
    """Groups files by filenames, changing only the netcdf variable name."""
    groups = []
    filenames = {f.name: f for f in files_list}

    for file in files_list:
        if file.name not in filenames:
            continue
        group = {}
        for variable in bccaq_variable_types:
            if variable in file.name:
                for other_var in bccaq_variable_types.difference([variable]):
                    other_filename = file.name.replace(variable, other_var)
                    if other_filename in filenames:
                        group[other_var] = filenames[other_filename]
                        del filenames[other_filename]
                if len(group):
                    # Found a match
                    group[variable] = file
                    del filenames[file.name]

                    if "tasmin" in group and "tasmax" in group:
                        group["tasmin"], group["tasmax"] = fix_broken_time_indices(
                            group["tasmin"], group["tasmax"]
                        )

                    groups.append(group)
                    break

    return groups


def make_ensemble(files: List[Path]) -> None:
    percentiles = [10, 50, 90]

    ensemble = ensembles.create_ensemble(files)
    # make sure we have data starting in 1950
    ensemble = ensemble.sel(time=(ensemble.time.dt.year >= 1950))
    ensemble_percentiles = ensembles.ensemble_percentiles(ensemble, values=percentiles)

    return ensemble_percentiles


def ensemble_to_netcdf(ensemble: xr.Dataset, output_path: Path) -> None:
    """Write an ensemble dataset to disk."""
    compression = {"zlib": True, "complevel": 1}

    encoding = {v: compression for v in ensemble.data_vars}
    encoding["time"] = {"dtype": "double"}

    ensemble.to_netcdf(str(output_path), format="NETCDF4", encoding=encoding)


def ensemble_common_handler(process: Process, request, response, subset_function):
    convert_to_csv = request.inputs["output_format"][0].data == "csv"
    if not convert_to_csv:
        del process.status_percentage_steps["convert_to_csv"]

    write_log(process, "Processing started", process_step="start")

    output_filename = make_output_filename(process, request.inputs)

    write_log(process, "Fetching BCCAQv2 datasets")

    rcp = single_input_or_none(request.inputs, "rcp")
    bccaqv2_inputs = get_bccaqv2_inputs(process.workdir, rcp=rcp)

    write_log(process, "Running subset", process_step="subset")

    subsetted_files = subset_function(
        process, netcdf_inputs=bccaqv2_inputs, request_inputs=request.inputs
    )

    if not subsetted_files:
        message = "No data was produced when subsetting using the provided bounds."
        raise ProcessError(message)

    write_log(process, "Computing indices", process_step="compute_indices")

    compute_inputs = {
        k: v for k, v in request.inputs.items() if k in process.xci_inputs_identifiers
    }

    input_groups = make_indicator_inputs(process.xci, compute_inputs, subsetted_files)
    n_groups = len(input_groups)

    indices_files = []

    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    for n, inputs in enumerate(input_groups):
        write_log(
            process,
            f"Computing indices for file {n + 1} of {n_groups}",
            subtask_percentage=n * 100 // n_groups,
        )
        output_ds = compute_indices(process, process.xci, inputs)

        output_name = f"{output_filename}_{process.identifier}_{n}.nc"
        for variable in bccaq_variable_types:
            if variable in inputs:
                input_name = Path(inputs.get(variable)[0].file).name
                output_name = input_name.replace(variable, process.identifier)

        output_path = Path(process.workdir) / output_name
        output_ds.to_netcdf(output_path)
        indices_files.append(output_path)

    warnings.filterwarnings("default", category=FutureWarning)
    warnings.filterwarnings("default", category=UserWarning)

    output_basename = Path(process.workdir) / (output_filename + "_ensemble")
    ensemble = make_ensemble(indices_files)

    if convert_to_csv:
        ensemble_csv = output_basename.with_suffix(".csv")
        df = dataset_to_dataframe(ensemble)
        df.to_csv(ensemble_csv)

        metadata = format_metadata(ensemble)
        metadata_file = output_basename.parent / f"{ensemble_csv.stem}_metadata.csv"
        metadata_file.write_text(metadata)

        ensemble_output = Path(process.workdir) / (output_filename + ".zip")
        zip_files(ensemble_output, [metadata_file, ensemble_csv])
    else:
        ensemble_output = output_basename.with_suffix(".nc")
        ensemble_to_netcdf(ensemble, ensemble_output)

    response.outputs["output"].file = ensemble_output

    write_log(process, "Processing finished successfully", process_step="done")
    return response
