# noqa: D100
import logging
import sys
import warnings
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd
import xarray as xr
from pandas.api.types import is_numeric_dtype
from parse import parse
from pywps import FORMATS, ComplexInput, Process
from pywps.app.exceptions import ProcessError
from pywps.exceptions import InvalidParameterValue
from siphon.catalog import TDSCatalog
from xclim import ensembles
from xclim.core.calendar import days_since_to_doy, doy_to_days_since, percentile_doy
from xclim.core.indicator import Indicator
from xclim.indicators.atmos import tg

from .subset import finch_subset_bbox, finch_subset_gridpoint, finch_subset_shape
from .utils import (
    DatasetConfiguration,
    PywpsInput,
    RequestInputs,
    compute_indices,
    dataset_to_dataframe,
    dataset_to_netcdf,
    format_metadata,
    get_datasets_config,
    iter_xc_variables,
    log_file_path,
    single_input_or_none,
    valid_filename,
    write_log,
    zip_files,
)
from .wps_base import make_nc_input

LOGGER = logging.getLogger("PYWPS")


def _percentile_doy(var: xr.DataArray, perc: int) -> xr.DataArray:
    return percentile_doy(var, per=perc).sel(percentiles=perc, drop=True)


variable_computations = {
    "tas": {"inputs": ["tasmin", "tasmax"], "args": [], "function": tg},
    "tasmax_per": {
        "inputs": ["tasmax"],
        "args": ["perc_tasmax"],
        "function": _percentile_doy,
    },
    "tasmin_per": {
        "inputs": ["tasmin"],
        "args": ["perc_tasmin"],
        "function": _percentile_doy,
    },
    "tas_per": {"inputs": ["tas"], "args": ["perc_tas"], "function": _percentile_doy},
    "pr_per": {"inputs": ["pr"], "args": ["perc_pr"], "function": _percentile_doy},
}


@dataclass
class Dataset:  # noqa: D101
    variable: str
    model: str
    scenario: str
    frequency: str = "day"
    realization: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None

    @classmethod
    def from_filename(cls, filename, pattern):  # noqa: D102
        match = parse(pattern, filename)
        if not match:
            return None
        return cls(**match.named)


def file_is_required(
    filename: str,
    pattern: str,
    model_lists: Optional[Dict[str, List[str]]] = None,
    variables: List[str] = None,
    scenario: str = None,
    models: List[Union[str, Tuple[str, int]]] = None,
):
    """Parse metadata and filter datasets."""
    file = Dataset.from_filename(filename, pattern)
    if not file:
        return False

    if variables and file.variable not in variables:
        return False

    if scenario and scenario not in file.scenario:
        return False

    if models is None or models[0].lower() == "all":
        return True

    if (
        len(models) == 1
        and isinstance(models[0], str)
        and model_lists is not None
        and models[0].lower() in model_lists
    ):
        models = model_lists[models[0]]

    for modelspec in models:
        if isinstance(modelspec, str):  # case with a single model name
            if file.model.lower() == modelspec.lower() and (
                file.realization is None or file.realization.startswith("r1i")
            ):
                return True
        else:  # case with a couple model name, realization num.
            if (
                file.model.lower() == modelspec[0].lower()
                and file.realization == modelspec[1]
            ):
                return True
    return False


def iter_remote(cat: TDSCatalog, depth: int = -1):
    """Create generator listing all datasets recursively in a TDSCatalog.

    The search is limited to a certain depth if `depth` >= 0.
    """
    for ds in cat.datasets.values():
        yield ds.name, ds.access_urls["OPENDAP"]

    if depth != 0:
        for subcat in cat.catalog_refs.values():
            yield from iter_remote(subcat.follow(), depth=depth - 1)


def iter_local(root: Path, depth: int = -1, pattern: str = "*.nc"):
    """Create generator listing all datasets recursively in a local directory.

    The search is limited to a certain depth if `depth` >= 0.
    The path can be given relative to the root finch code repo.
    """
    if not root.is_absolute():
        root = (Path(__file__).parent.parent / root).resolve()

    for file in root.glob(pattern):
        yield file.name, file

    if depth != 0:
        for sub in root.iterdir():
            if sub.is_dir():
                yield from iter_local(sub, depth=depth - 1, pattern=pattern)


def _make_resource_input(url: str, workdir: str, local: bool):
    inp = ComplexInput(
        "resource",
        "NetCDF resource",
        max_occurs=1000,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    )
    inp.workdir = workdir
    if local:
        inp.file = url
    else:
        inp.url = url
    return inp


def get_datasets(
    dsconf: DatasetConfiguration,
    workdir: str,
    variables: Optional[List[str]] = None,
    scenario: Optional[str] = None,
    models: Optional[List[str]] = None,
) -> List[PywpsInput]:
    """Parse a directory to find files and filters the list to return only the needed ones, as resource inputs.

    Parameters
    ----------
    dsconf : DatasetConfiguration
        The dataclass defining a specific ensemble dataset.
    workdir: str
        The working directory where files will be downloaded if needed.
    variables: list of strings
        A list of the needed variables
    scenario: str
        The name of the scenario (experiment), rcps or ssps.
    models: list of strings
        A list of the requested models (or name of a models sublist)
    """
    if dsconf.local:
        iterator = iter_local(Path(dsconf.path), dsconf.depth, dsconf.suffix)
    else:
        iterator = iter_remote(TDSCatalog(dsconf.path), depth=dsconf.depth)

    inputs = []
    for name, url in iterator:
        if file_is_required(
            name,
            dsconf.pattern,
            dsconf.model_lists,
            variables=variables,
            scenario=scenario,
            models=models,
        ):
            inputs.append(_make_resource_input(url, workdir, dsconf.local))
    return inputs


def _formatted_coordinate(value) -> Optional[str]:
    """Return the first float value.

    The value can be a comma separated list of floats or a single float.
    """
    if not value:
        return
    try:
        value = value.split(",")[0]
    except AttributeError:
        pass
    return f"{float(value):.3f}"


def make_output_filename(
    process: Process, inputs: List[PywpsInput], scenario=None, dataset=None
):
    """Return a filename for the process's output, depending on its inputs.

    The scenario part of the filename can be overriden.
    """
    if scenario is None:
        scenario = single_input_or_none(inputs, "scenario")
    if dataset is None:
        dataset = single_input_or_none(inputs, "dataset")
    lat = _formatted_coordinate(single_input_or_none(inputs, "lat"))
    lon = _formatted_coordinate(single_input_or_none(inputs, "lon"))
    lat0 = _formatted_coordinate(single_input_or_none(inputs, "lat0"))
    lon0 = _formatted_coordinate(single_input_or_none(inputs, "lon0"))
    lat1 = _formatted_coordinate(single_input_or_none(inputs, "lat1"))
    lon1 = _formatted_coordinate(single_input_or_none(inputs, "lon1"))

    # Get given prefix and if none given, default to the identifier.
    output_parts = []

    if prefix := single_input_or_none(inputs, "output_name"):
        output_parts.append(prefix)
    else:
        if dataset:
            output_parts.append(dataset)
        output_parts.append(process.identifier)

    if lat and lon:
        output_parts.extend([lat, lon])
    elif lat0 and lon0:
        output_parts.extend([lat0, lon0])

    if lat1 and lon1:
        output_parts.extend([lat1, lon1])

    if isinstance(scenario, str):
        output_parts.append(scenario)
    elif scenario:
        output_parts.extend(scenario)

    return valid_filename("_".join(output_parts) + ".nc")


def uses_accepted_netcdf_variables(
    indicator: Indicator, available_variables: set
) -> bool:
    """Determine if indicator uses accepted NetCDF variables.

    Returns
    -------
    bool
        True if this indicator uses variables available by computation or in any dataset.
        This means it may return indicators that are not compatible with all datasets.
    """
    return all(
        n in available_variables or n in variable_computations
        for n in iter_xc_variables(indicator)
    )


def make_indicator_inputs(
    indicator: Indicator, wps_inputs: RequestInputs, files_list: List[Path]
) -> List[RequestInputs]:
    """From a list of files, make a list of inputs used to call the given xclim indicator."""
    required_netcdf_args = set(iter_xc_variables(indicator))

    input_list = []

    if len(required_netcdf_args) == 1:
        variable_name = list(required_netcdf_args)[0]
        for path in files_list:
            inputs = deepcopy(wps_inputs)
            inputs[variable_name] = deque([make_nc_input(variable_name)])
            inputs[variable_name][0].file = str(path)
            input_list.append(inputs)
    else:
        for group in make_file_groups(files_list, required_netcdf_args):
            inputs = deepcopy(wps_inputs)
            for variable_name, path in group.items():
                if variable_name not in required_netcdf_args:
                    continue
                inputs[variable_name] = deque([make_nc_input(variable_name)])
                inputs[variable_name][0].file = str(path)
            input_list.append(inputs)

    return input_list


def make_file_groups(files_list: List[Path], variables: set) -> List[Dict[str, Path]]:
    """Group files by filenames, changing only the netcdf variable name.

    The list of variable names to search must be given.
    """
    groups = []
    filenames = {f.name: f for f in files_list}

    for file in files_list:
        if file.name not in filenames:
            continue
        group = {}
        for variable in variables:
            if (
                file.name.startswith(f"{variable.lower()}_")
                or f"_{variable.lower()}_" in file.name
            ):
                for other_var in variables.difference({variable}):
                    other_filename = file.name.replace(variable, other_var, 1)
                    if other_filename in filenames:
                        group[other_var] = filenames[other_filename]
                        del filenames[other_filename]

                group[variable] = file
                del filenames[file.name]
                groups.append(group)
                break

    return groups


def make_ensemble(
    files: List[Path], percentiles: List[int], average_dims: Optional[Tuple[str]] = None
) -> None:  # noqa: D103
    ensemble = ensembles.create_ensemble(
        files, realizations=[file.stem for file in files]
    )
    # make sure we have data starting in 1950
    ensemble = ensemble.sel(time=(ensemble.time.dt.year >= 1950))

    # If data is in day of year, percentiles won't make sense.
    # Convert to "days since" (base will be the time coordinate)
    for v in ensemble.data_vars:
        if ensemble[v].attrs.get("is_dayofyear", 0) == 1:
            ensemble[v] = doy_to_days_since(ensemble[v])

    if average_dims is not None:
        ensemble = ensemble.mean(dim=average_dims)

    if percentiles:
        ensemble_percentiles = ensembles.ensemble_percentiles(
            ensemble, values=percentiles
        )
    else:
        ensemble_percentiles = ensemble

    # Doy data converted previously is converted back.
    for v in ensemble_percentiles.data_vars:
        if ensemble_percentiles[v].attrs.get("units", "").startswith("days after"):
            ensemble_percentiles[v] = days_since_to_doy(ensemble_percentiles[v])

    # Depending on the datasets, I've found that writing the netcdf could hang
    # if the dataset was not loaded explicitely previously... Not sure why.
    # The datasets should be pretty small when computing the ensembles, so this is
    # a best effort at working around what looks like a bug in either xclim or xarray.
    # The xarray documentation mentions: 'this method can be necessary when working
    # with many file objects on disk.'
    # ensemble_percentiles.load()

    return ensemble_percentiles


def compute_intermediate_variables(
    files_list: List[Path],
    variables: set,
    required_variable_names: Iterable[str],
    workdir: Path,
    request_inputs,
) -> List[Path]:
    """Compute netcdf datasets from a list of required variable names and existing files."""
    output_files_list = []
    file_groups = make_file_groups(files_list, variables)
    for group in file_groups:
        # add file paths that are required without any computation
        for variable, path in group.items():
            if variable in required_variable_names:
                output_files_list.append(path)

        first_variable = list(group)[0]
        output_basename = group[first_variable].name.split("_", 1)[1]

        # compute other required variables
        variables_to_compute = set(required_variable_names) - set(group)

        # add intermediate files to compute (ex: tas is needed for tn10)
        for variable in list(variables_to_compute):
            for input_name in variable_computations[variable]["inputs"]:
                if input_name in variable_computations:
                    variables_to_compute.add(input_name)

        while variables_to_compute:
            for variable in list(variables_to_compute):
                input_names = variable_computations[variable]["inputs"]
                arg_names = variable_computations[variable]["args"]
                if all(i in group for i in input_names) and all(
                    a in request_inputs for a in arg_names
                ):
                    inputs = [
                        xr.open_dataset(group[name])[name] for name in input_names
                    ]
                    args = [
                        single_input_or_none(request_inputs, name) for name in arg_names
                    ]

                    output = variable_computations[variable]["function"](
                        *inputs, *args
                    ).to_dataset(name=variable)
                    output_file = Path(workdir) / f"{variable}_{output_basename}"
                    dataset_to_netcdf(output, output_file)

                    variables_to_compute.remove(variable)
                    group[variable] = output_file
                    if variable in required_variable_names:
                        output_files_list.append(output_file)
                    break
            else:
                raise RuntimeError(
                    f"Cant compute intermediate variables {variables_to_compute}"
                )

    return output_files_list


def get_input_lists(needed: set, available: set):
    """From a list of dataset variables, get the source variable names to compute them."""
    raw = available.intersection(needed)
    unknown = needed.difference(raw)
    compute = set()
    extra = set()

    while unknown:
        for var in list(unknown):
            if var in variable_computations:
                this_needed = set(variable_computations[var]["inputs"])
                compute.add(var)
                unknown.remove(var)
                raw.update(this_needed.intersection(available))
                unknown.update(this_needed.difference(available))
            else:
                unknown.remove(var)
                extra.add(var)
    return raw, compute, extra


def ensemble_common_handler(
    process: Process, request, response, subset_function
):  # noqa: D103
    assert subset_function in [
        finch_subset_bbox,
        finch_subset_gridpoint,
        finch_subset_shape,
    ]

    xci_inputs = process.xci_inputs_identifiers
    request_inputs_not_datasets = {
        k: v
        for k, v in request.inputs.items()
        if k in xci_inputs and not k.startswith("perc")
    }

    dataset_name = single_input_or_none(request.inputs, "dataset")
    dataset = get_datasets_config()[dataset_name]

    needed_variables = set(iter_xc_variables(process.xci))
    avail_variables = set(dataset.allowed_values["variable"])
    source_variables, computed_variables, extra_variables = get_input_lists(
        needed_variables, avail_variables
    )

    scenarios = [r.data.strip() for r in request.inputs["scenario"]]
    models = [m.data.strip() for m in request.inputs["models"]]

    # Check if arguments are ok for this dataset
    if not set(dataset.allowed_values["scenario"]).issuperset(scenarios):
        raise InvalidParameterValue(
            f"Invalid scenarios for dataset {dataset_name}. "
            f"Should be in {dataset.allowed_values['scenario']}."
        )
    if (
        not set(dataset.allowed_values["model"])
        .union(dataset.model_lists.keys())
        .union({"all"})
        .issuperset(models)
    ):
        raise InvalidParameterValue(
            f"Invalid models or model list for dataset {dataset_name}. "
            f"Should be in {dataset.allowed_values['model']} + {list(dataset.model_lists.keys())}"
        )
    if extra_variables:
        raise InvalidParameterValue(
            f"The {process.xci.identifier} indicator cannot be used with dataset {dataset_name}"
            f" because it does not provide the variables {extra_variables} or doesn't provide "
            "the variable that could be used to compute those."
        )

    convert_to_csv = request.inputs["output_format"][0].data == "csv"
    if not convert_to_csv:
        del process.status_percentage_steps["convert_to_csv"]
    percentiles_string = request.inputs["ensemble_percentiles"][0].data
    ensemble_percentiles = (
        [int(p.strip()) for p in percentiles_string.split(",")]
        if percentiles_string != "None"
        else []
    )

    write_log(
        process,
        f"Processing started ({len(scenarios)} scenarios)",
        process_step="start",
    )

    if single_input_or_none(request.inputs, "average"):
        if subset_function == finch_subset_gridpoint:
            average_dims = ("region",)
        else:
            average_dims = ("lat", "lon")
    else:
        average_dims = None
    write_log(process, f"Will average over {average_dims}")

    base_work_dir = Path(process.workdir)
    ensembles = []
    output_basename = Path(
        make_output_filename(
            process, request.inputs, scenario=scenarios, dataset=dataset_name
        )
    )
    for scenario in scenarios:
        # Ensure no file name conflicts (i.e. if the scenario doesn't appear in the base filename)
        work_dir = base_work_dir / scenario
        work_dir.mkdir(exist_ok=True)
        process.set_workdir(str(work_dir))

        write_log(process, f"Fetching datasets for scenario {scenario}")
        netcdf_inputs = get_datasets(
            dataset,
            workdir=process.workdir,
            variables=list(source_variables),
            scenario=scenario,
            models=models,
        )

        if len(netcdf_inputs) == 0:
            raise ValueError(
                f"No netCDF files were selected with filters {scenario=}, {models=} and variables={source_variables}"
            )

        write_log(process, f"Running subset scen={scenario}", process_step="subset")
        subsetted_files = subset_function(
            process, netcdf_inputs=netcdf_inputs, request_inputs=request.inputs
        )
        if not subsetted_files:
            message = "No data was produced when subsetting using the provided bounds."
            raise ProcessError(message)

        subsetted_intermediate_files = compute_intermediate_variables(
            subsetted_files,
            source_variables,
            needed_variables,
            process.workdir,
            request.inputs,
        )
        write_log(
            process,
            f"Computing indices scen={scenario}",
            process_step="compute_indices",
        )

        print(subsetted_intermediate_files, file=sys.stderr)
        input_groups = make_indicator_inputs(
            process.xci, request_inputs_not_datasets, subsetted_intermediate_files
        )
        n_groups = len(input_groups)

        indices_files = []

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)

        for n, inputs in enumerate(input_groups):
            write_log(
                process,
                f"Computing indices for file {n + 1} of {n_groups}, scen={scenario}",
                subtask_percentage=n * 100 // n_groups,
            )
            output_ds = compute_indices(process, process.xci, inputs)
            for variable in needed_variables:
                input_name = Path(inputs[variable][0].file).name
                output_name = input_name.replace(variable, process.identifier)

            output_path = Path(process.workdir) / output_name
            dataset_to_netcdf(output_ds, output_path)
            indices_files.append(output_path)

        warnings.filterwarnings("default", category=FutureWarning)
        warnings.filterwarnings("default", category=UserWarning)

        ensemble = make_ensemble(indices_files, ensemble_percentiles, average_dims)
        ensemble.attrs["source_datasets"] = "\n".join(
            [dsinp.url for dsinp in netcdf_inputs]
        )
        ensembles.append(ensemble)

    process.set_workdir(str(base_work_dir))

    if "realization" in ensembles[0].dims and len(scenarios) > 1:
        # For non-reducing calls with multiple scenarios, remove the scenario information from the member name.
        for scen, ds in zip(scenarios, ensembles):
            ds["realization"] = [
                real.replace(scen, "") for real in ds.realization.values
            ]

    ensemble = xr.concat(
        ensembles, dim=xr.DataArray(scenarios, dims=("scenario",), name="scenario")
    )

    if convert_to_csv:
        ensemble_csv = output_basename.with_suffix(".csv")
        prec = single_input_or_none(request.inputs, "csv_precision")
        if prec and prec < 0:
            ensemble = ensemble.round(prec)
            prec = 0
        df = dataset_to_dataframe(ensemble)
        if average_dims is None:
            dims = ["lat", "lon", "time"]
        else:
            dims = ["time"]
        df = df.reset_index().set_index(dims)
        if "region" in df.columns:
            df.drop(columns="region", inplace=True)

        if prec is not None:
            for v in df:
                if v not in dims and is_numeric_dtype(df[v]):
                    df[v] = df[v].map(
                        lambda x: f"{x:.{prec}f}" if not pd.isna(x) else ""
                    )

        df.to_csv(ensemble_csv)

        metadata = format_metadata(ensemble)
        metadata_file = output_basename.parent / f"{output_basename}_metadata.txt"
        metadata_file.write_text(metadata)

        ensemble_output = Path(process.workdir) / output_basename.with_suffix(".zip")
        zip_files(ensemble_output, [metadata_file, ensemble_csv])
    else:
        LOGGER.info(output_basename)
        ensemble_output = output_basename.with_suffix(".nc")
        dataset_to_netcdf(ensemble, ensemble_output)

    response.outputs["output"].file = ensemble_output
    response.outputs["output_log"].file = str(log_file_path(process))

    write_log(
        process,
        f"Processing finished successfully : {ensemble_output}",
        process_step="done",
    )
    return response
