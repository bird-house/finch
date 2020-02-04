from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union

from pywps import ComplexInput, FORMATS, Process
from pywps import configuration
from siphon.catalog import TDSCatalog
import xarray as xr
from xclim.checks import assert_daily

from .utils import PywpsInput
from .utils import single_input_or_none


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


def get_bccaqv2_inputs(wps_inputs, variable=None, rcp=None, catalog_url=None):
    """Adds a 'resource' input list with bccaqv2 urls to WPS inputs."""
    catalog_url = configuration.get_config_value("finch", "bccaqv2_url")
    new_inputs = deepcopy(wps_inputs)
    workdir = next(iter(wps_inputs.values()))[0].workdir

    new_inputs["resource"] = []

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
            new_inputs["resource"].append(resource)
    else:
        for file in get_bccaqv2_local_files_datasets(catalog_url, variable, rcp):
            resource = _make_bccaqv2_resource_input()
            resource.file = file
            resource.workdir = workdir
            new_inputs["resource"].append(resource)

    return new_inputs


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
