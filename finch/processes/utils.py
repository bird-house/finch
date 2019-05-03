from typing import List

import requests
from siphon.catalog import TDSCatalog


def is_opendap_url(url):
    if url and not url.startswith("file"):
        r = requests.get(url + ".dds")
        if r.status_code == 200 and r.content.decode().startswith("Dataset"):
            return True
    return False


def get_bcca2v2_opendap_datasets(catalog_url, variable, rcp) -> List[str]:
    """Get a list of urls corresponding to variable and rcp on a Thredds server.

    We assume that the files are named in a certain way on the Thredds server.

    This is the case for boreas.ouranos.ca/thredds
    For more general use cases, see the `xarray` and `requests` methods below."""
    catalog = TDSCatalog(catalog_url)

    urls = []

    for dataset in catalog.datasets.values():
        opendap_url = dataset.access_urls["OPENDAP"]

        if variable in dataset.name and dataset.name.startswith(rcp):
            urls.append(opendap_url)

        # using requests (a bit slower, and the Thredds server didn't seem to like it)
        # r = requests.get(opendap_url + ".das").content.decode()
        # for line in r.split("\n"):
        #     match = re.search(r'String driving_experiment_id "(.+)"', line)
        #     if match and rcp in match.group(1).split(","):
        #         urls.append(opendap_url)
        #         print(opendap_url)

        # using xarray (still a bit slower, like 2 secs per dataset)
        # ds = xr.open_dataset(opendap_url, decode_times=False)
        # rcps = [r for r in ds.attrs.get('driving_experiment_id', '').split(',') if 'rcp' in r]
        # if rcp in rcps and variable in ds.data_vars:
        #     urls.append(opendap_url)

    return urls
