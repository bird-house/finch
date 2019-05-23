import re
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

bccaqv2_link = (
    "https://boreas.ouranos.ca/thredds/catalog/birdhouse/pcic/BCCAQv2/catalog.xml"
)
BCCAQV2_LIMIT = 3  # Todo: remove-me. Temporary limit the number of datasets to request


def is_opendap_url(url):
    if url and not url.startswith("file"):
        r = requests.get(url + ".dds")
        if r.status_code == 200 and r.content.decode().startswith("Dataset"):
            return True
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

        variable_ok = variable is None
        rcp_ok = rcp is None

        if method == ParsingMethod.filename:
            variable_ok = variable_ok or dataset.name.startswith(variable)
            rcp_ok = rcp_ok or rcp in dataset.name

        elif method == ParsingMethod.opendap_das:
            re_experiment = re.compile(r'String driving_experiment_id "(.+)"')
            lines = requests.get(opendap_url + ".das").content.decode().split("\n")

            variable_ok = variable_ok or any(
                line.startswith(f"    {variable} {{") for line in lines
            )
            if not rcp_ok:
                for line in lines:
                    match = re_experiment.search(line)
                    if match and rcp in match.group(1).split(","):
                        rcp_ok = True

        elif method == ParsingMethod.xarray:
            import xarray as xr

            ds = xr.open_dataset(opendap_url, decode_times=False)
            rcps = [
                r
                for r in ds.attrs.get("driving_experiment_id", "").split(",")
                if "rcp" in r
            ]
            variable_ok = variable_ok or variable in ds.data_vars
            rcp_ok = rcp_ok or rcp in rcps

        if variable_ok and rcp_ok:
            urls.append(opendap_url)
    urls = urls[:BCCAQV2_LIMIT]  # Todo: remove-me
    return urls


def get_bccaqv2_inputs(wps_inputs, variable=None, rcp=None, catalog_url=bccaqv2_link):
    """Adds a 'resource' input list with bccaqv2 urls to WPS inputs."""
    new_inputs = deepcopy(wps_inputs)
    workdir = next(iter(wps_inputs.values()))[0].workdir

    new_inputs["resource"] = []
    for url in get_bccaqv2_opendap_datasets(catalog_url, variable, rcp):
        resource = _make_bccaqv2_resource_input(url)
        resource.workdir = workdir
        new_inputs["resource"].append(resource)

    return new_inputs


def _make_bccaqv2_resource_input(url):
    input = ComplexInput(
        "resource",
        "NetCDF resource",
        max_occurs=1000,
        supported_formats=[FORMATS.NETCDF, FORMATS.DODS],
    )
    input.url = url
    return input


def netcdf_to_csv(
    netcdf_files, output_folder, filename_prefix
) -> Tuple[List[str], str]:
    """Write csv files for a list of netcdf files.

    Produces one csv file per calendar type, along with a metadata folder in
    the output_folder."""
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    metadata = {}
    concat_by_calendar = {}
    for file in netcdf_files:
        ds = xr.open_dataset(file, decode_times=False)
        calendar = ds.time.calendar
        ds["time"] = xr.decode_cf(ds).time

        for variable in ds.data_vars:
            model = ds.attrs["driving_model_id"]
            experiment = ds.attrs["driving_experiment_id"].replace(",", "_")
            units = ds[variable].units

            output_variable = f"{variable}_{model}_{experiment}_({units})"
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
