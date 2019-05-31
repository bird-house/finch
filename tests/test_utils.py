import shutil
import zipfile
from pathlib import Path

from pywps import configuration

from finch.processes.utils import get_bccaqv2_opendap_datasets, netcdf_to_csv, zip_files
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

    netcdf_files = list(folder.glob("*.nc"))
    csv_files, metadata = netcdf_to_csv(netcdf_files, output_folder, "file_prefix")

    output_zip = output_folder / "output.zip"
    files = csv_files + [metadata]
    zip_files(output_zip, files)

    with zipfile.ZipFile(output_zip) as z:
        assert len(z.infolist()) == 237
        assert sum(1 for f in z.infolist() if f.filename.startswith("metadata")) == 233
