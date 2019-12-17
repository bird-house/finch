import shutil
import zipfile
from pathlib import Path

from pywps import configuration

from finch.processes.utils import (
    get_bccaqv2_opendap_datasets,
    netcdf_to_csv,
    zip_files,
    is_opendap_url,
)
import pytest
from unittest import mock


@mock.patch("finch.processes.utils.TDSCatalog")
def test_get_opendap_datasets_bccaqv2(mock_tdscatalog):
    names = [
        "tasmin_day_BCCAQv2+ANUSPLIN300_CNRM-CM5_historical+rcp85_r1i1p1_19500101-21001231.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_CNRM-CM5_historical+rcp45_r1i1p1_19500101-21001231.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_CanESM2_historical+rcp45_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_CanESM2_historical+rcp45_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-M_historical+rcp26_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp85_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp45_r1i1p1_19500101-21001231.",
    ]
    catalog_url = configuration.get_config_value("finch", "bccaqv2_url")
    variable = "tasmin"
    rcp = "rcp45"

    mock_catalog = mock.MagicMock()
    mock_tdscatalog.return_value = mock_catalog

    def make_dataset(name):
        dataset = mock.MagicMock()
        dataset.access_urls = {"OPENDAP": "url"}
        dataset.name = name
        return dataset

    mock_catalog.datasets = {name: make_dataset(name) for name in names}

    urls = get_bccaqv2_opendap_datasets(catalog_url, variable, rcp)
    assert len(urls) == 2


def test_netcdf_to_csv_to_zip():
    here = Path(__file__).parent
    folder = here / "data" / "bccaqv2_single_cell"
    output_folder = here / "tmp" / "tasmin_csvs"
    shutil.rmtree(output_folder, ignore_errors=True)

    netcdf_files = list(sorted(folder.glob("tasmin*.nc")))
    # only take a small subset of files that have all the calendar types
    netcdf_files = netcdf_files[:5] + netcdf_files[40:50]
    csv_files, metadata = netcdf_to_csv(netcdf_files, output_folder, "file_prefix")

    output_zip = output_folder / "output.zip"
    files = csv_files + [metadata]
    zip_files(output_zip, files)

    with zipfile.ZipFile(output_zip) as z:
        n_calendar_types = 4
        n_files = 15
        assert len(z.infolist()) == n_files + n_calendar_types
        assert sum(1 for f in z.infolist() if f.filename.startswith("metadata")) == n_files


def test_is_opendap_url():
    # This test uses online requests, but the links shoudl be pretty stable.
    # In case the link are no longer available, we should change the url.
    # This is better than skipping this test in CI.

    url = (
        "https://boreas.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/"
        "birdhouse/nrcan/nrcan_canada_daily_v2/tasmin/nrcan_canada_daily_tasmin_2017.nc"
    )
    assert is_opendap_url(url)

    url = url.replace("dodsC", "fileServer")
    assert not is_opendap_url(url)

    # no Content-Description header
    url = "http://test.opendap.org/opendap/netcdf/examples/tos_O1_2001-2002.nc"
    assert is_opendap_url(url)

    url = "invalid_schema://something"
    assert not is_opendap_url(url)

    url = "https://www.example.com"
    assert not is_opendap_url(url)

    url = "/missing_schema"
    assert not is_opendap_url(url)
