import re
from copy import deepcopy

from typing import List
from enum import Enum

import requests
from pywps import ComplexInput, FORMATS
from siphon.catalog import TDSCatalog

bccaqv2_link = "https://boreas.ouranos.ca/thredds/catalog/birdhouse/pcic/BCCAQv2/catalog.xml"
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

            variable_ok = variable_ok or any(line.startswith(f"    {variable} {{") for line in lines)
            if not rcp_ok:
                for line in lines:
                    match = re_experiment.search(line)
                    if match and rcp in match.group(1).split(","):
                        rcp_ok = True

        elif method == ParsingMethod.xarray:
            import xarray as xr

            ds = xr.open_dataset(opendap_url, decode_times=False)
            rcps = [r for r in ds.attrs.get('driving_experiment_id', '').split(',') if 'rcp' in r]
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
