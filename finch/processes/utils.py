import re

import requests
from siphon.catalog import TDSCatalog


def is_opendap_url(url):
    if url and not url.startswith("file"):
        r = requests.get(url + ".dds")
        if r.status_code == 200 and r.content.decode().startswith("Dataset"):
            return True
    return False


def get_opendap_datasets(catalog_url, variable, rcp):
    catalog = TDSCatalog(catalog_url)

    urls = []

    for dataset in catalog.datasets.values():
        if variable in dataset.name and rcp in dataset.name:
            urls.append(dataset.access_urls["OPENDAP"])

        ## using requests (a bit slower, and the Thredds server didn't seem to like it)
        # opendap_url = dataset.access_urls["OPENDAP"]
        # r = requests.get(opendap_url + ".das").content.decode()
        # for line in r.split("\n"):
        #     match = re.search(r'String driving_experiment_id "(.+)"', line)
        #     if match and rcp in match.group(1).split(","):
        #         urls.append(opendap_url)
        #         print(opendap_url)

        ## using xarray (still a bit slower, like 2 secs per dataset)
        # ds = xr.open_dataset(opendap_url, decode_times=False)
        # rcps = [r for r in ds.attrs.get('driving_experiment_id', '').split(',') if 'rcp' in r]
        # if rcp in rcps and variable in ds.data_vars:
            # urls.append(opendap_url)

    return urls
