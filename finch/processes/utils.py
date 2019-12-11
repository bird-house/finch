import re
import time
import zipfile
from copy import deepcopy
from pathlib import Path

from typing import List, Tuple
from enum import Enum

import pandas as pd
import xarray as xr
import requests
from pywps import ComplexInput, FORMATS
from siphon.catalog import TDSCatalog
from pywps import configuration


def is_opendap_url(url):
    """
    Check if a provided url is an OpenDAP url.

    The OpenDAP server should provide a Dataset Descriptor Structure (DDS) at the *.dds url.
    We try to get this url by appending the suffix, and inspect the reponse to see if it's an OpenDAP response.
    One downside of this method is that the provided url could contain query parameters, or special
    OpenDAP syntax after the filename, so appending .dds will not create a valid url.

    Sometimes, a Thredds server can become unresponsive when we send too many requests.
    In those cases, we get a requests.exceptions.ConnectionError.
    We retry a couple times with exponential backoff.
    """
    retry = 3
    if url and not url.startswith("file"):
        while retry:
            try:
                r = requests.get(url + ".dds", timeout=2)
            except requests.exceptions.ConnectionError:
                time.sleep(10 // retry ** 2)
                retry -= 1
                continue
            except requests.exceptions.MissingSchema:
                # most likely a local file
                break
            if r.status_code == 200 and r.content.decode().startswith("Dataset"):
                return True
            break
    return False


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

        re_experiment = re.compile(r'String driving_experiment_id "(.+)"')
        lines = requests.get(url + ".das").content.decode().split("\n")
        variable_ok = variable_ok or any(
            line.startswith(f"    {variable} {{") for line in lines
        )
        if not rcp_ok:
            for line in lines:
                match = re_experiment.search(line)
                if match and rcp in match.group(1).split(","):
                    rcp_ok = True

    elif method == ParsingMethod.xarray:

        raise NotImplementedError("todo: filter models and runs")

        import xarray as xr

        ds = xr.open_dataset(url, decode_times=False)
        rcps = [
            r
            for r in ds.attrs.get("driving_experiment_id", "").split(",")
            if "rcp" in r
        ]
        variable_ok = variable_ok or variable in ds.data_vars
        rcp_ok = rcp_ok or rcp in rcps

    return rcp_ok and variable_ok


def get_bccaqv2_inputs(wps_inputs, variable=None, rcp=None, catalog_url=None):
    """Adds a 'resource' input list with bccaqv2 urls to WPS inputs."""
    catalog_url = configuration.get_config_value("finch", "bccaqv2_url")
    new_inputs = deepcopy(wps_inputs)
    workdir = next(iter(wps_inputs.values()))[0].workdir

    new_inputs["resource"] = []

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


def _make_bccaqv2_resource_input():
    input = ComplexInput(
        "resource",
        "NetCDF resource",
        max_occurs=1000,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    )
    return input


def netcdf_to_csv(
    netcdf_files, output_folder, filename_prefix
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
        ds = xr.open_dataset(file, decode_times=False)
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

            df = ds.to_dataframe()[["lat", "lon", output_variable]]
            # most runs have timestamp with hour == 12 a few hour == 0 .. make uniform
            df.index = df.index.map(lambda x: x.replace(hour=12))

            if calendar not in concat_by_calendar:
                concat_by_calendar[calendar] = [df]
            else:
                concat_by_calendar[calendar].append(df[output_variable])

            metadata[output_variable] = format_metadata(ds)

    output_csv_list = []
    for calendar_type, data in concat_by_calendar.items():
        output_csv = output_folder / f"{filename_prefix}_{calendar_type}.csv"
        pd.concat(data, axis=1).to_csv(output_csv)
        output_csv_list.append(output_csv)

    metadata_folder = output_folder / "metadata"
    metadata_folder.mkdir(parents=True, exist_ok=True)
    for output_variable, info in metadata.items():
        metadata_file = metadata_folder / f"{output_variable}.csv"
        metadata_file.write_text(info)

    return output_csv_list, metadata_folder


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


def zip_files(output_filename, files=None, log_function=None, start_percentage=90):
    """Create a zipfile from a list of files or folders.

    log_function is a function that receives a message and a percentage."""
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
            if log_function is not None:
                percentage = start_percentage + int(
                    n / n_files * (100 - start_percentage)
                )
                message = f"Zipping file {n + 1} of {n_files}"
                log_function(message, percentage)
            arcname = filename.relative_to(common_folder) if common_folder else None
            z.write(filename, arcname=arcname)
