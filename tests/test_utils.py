from finch.processes.constants import ALL_24_MODELS, PCIC_12
from pathlib import Path
import shutil
from unittest import mock
import zipfile

import numpy as np
import pandas as pd
import pytest
from pywps import configuration
import xarray as xr

from finch.processes import ensemble_utils
from finch.processes.ensemble_utils import get_bccaqv2_opendap_datasets
from finch.processes.utils import (
    drs_filename,
    is_opendap_url,
    netcdf_file_list_to_csv,
    zip_files,
)

test_data = Path(__file__).parent / "data"


@mock.patch("finch.processes.ensemble_utils.TDSCatalog")
def test_get_opendap_datasets_bccaqv2(mock_tdscatalog):
    names = [
        "tasmin_day_BCCAQv2+ANUSPLIN300_CNRM-CM5_historical+rcp85_r1i1p1_19500101-21001231.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_CNRM-CM5_historical+rcp45_r1i1p1_19500101-21001231.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_CanESM2_historical+rcp45_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_CanESM2_historical+rcp45_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-M_historical+rcp26_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp85_r1i1p1_19500101-21001231.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp45_r1i1p1_19500101-21001231.nc",
    ]
    catalog_url = configuration.get_config_value("finch", "dataset_bccaqv2")
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

    urls = get_bccaqv2_opendap_datasets(catalog_url, [variable], rcp)
    assert len(urls) == 2


def test_netcdf_file_list_to_csv_to_zip():
    here = Path(__file__).parent
    folder = here / "data" / "bccaqv2_single_cell"
    output_folder = here / "tmp" / "tasmin_csvs"
    shutil.rmtree(output_folder, ignore_errors=True)

    netcdf_files = list(sorted(folder.glob("tasmin*.nc")))
    # only take a small subset of files that have all the calendar types
    netcdf_files = netcdf_files[:5] + netcdf_files[40:50]
    csv_files, metadata = netcdf_file_list_to_csv(
        netcdf_files, output_folder, "file_prefix"
    )

    output_zip = output_folder / "output.zip"
    files = csv_files + [metadata]
    zip_files(output_zip, files)

    with zipfile.ZipFile(output_zip) as z:
        n_calendar_types = 4
        n_files = len(netcdf_files)
        data_filenames = [n for n in z.namelist() if "metadata" not in n]
        metadata_filenames = [n for n in z.namelist() if "metadata" in n]

        assert len(z.namelist()) == n_files + n_calendar_types
        assert len(metadata_filenames) == n_files
        for filename in data_filenames:
            csv_lines = z.read(filename).decode().split("\n")[1:-1]
            n_lines = len(csv_lines)
            n_columns = len(csv_lines[0].split(",")) - 3

            if "proleptic_gregorian" in filename:
                assert n_lines == 366
                assert n_columns == 2
            elif "365_day" in filename:
                assert n_lines == 365
                assert n_columns == 8
            elif "360_day" in filename:
                assert n_lines == 360
                assert n_columns == 3
            elif "standard" in filename:
                assert n_lines == 366
                assert n_columns == 2
            else:
                assert False, "Unknown calendar type"


def test_netcdf_file_list_to_csv_bad_hours():
    here = Path(__file__).parent
    folder = here / "data" / "bccaqv2_single_cell"
    output_folder = here / "tmp" / "tasmin_csvs"
    shutil.rmtree(output_folder, ignore_errors=True)

    # these files contain an hour somewhere at 0 (midnight) it should be 12h
    bad_hours = [
        "pr_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp26_r1i1p1_19500101-21001231_sub.nc",
        "pr_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp45_r1i1p1_19500101-21001231_sub.nc",
        "pr_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp85_r1i1p1_19500101-21001231_sub.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp26_r1i1p1_19500101-21001231_sub.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp45_r1i1p1_19500101-21001231_sub.nc",
        "tasmax_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp85_r1i1p1_19500101-21001231_sub.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp26_r1i1p1_19500101-21001231_sub.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp45_r1i1p1_19500101-21001231_sub.nc",
        "tasmin_day_BCCAQv2+ANUSPLIN300_NorESM1-ME_historical+rcp85_r1i1p1_19500101-21001231_sub.nc",
    ]
    netcdf_files = [folder / bad for bad in bad_hours]

    csv_files, _ = netcdf_file_list_to_csv(netcdf_files, output_folder, "file_prefix")

    for csv in csv_files:
        df = pd.read_csv(csv, parse_dates=["time"])
        assert np.all(df.time.dt.hour == 12)


@pytest.mark.online
def test_is_opendap_url():
    # This test uses online requests, and the servers are not as stable as hoped.
    # We should record these requests so that the tests don't break when the servers are down.

    url = (
        "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/"
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


def test_bccaqv2_make_file_groups():
    folder = Path(__file__).parent / "data" / "bccaqv2_single_cell"
    files_list = list(folder.glob("*.nc"))
    groups = ensemble_utils.make_file_groups(files_list)

    assert len(groups) == 85
    assert all(len(g) == 3 for g in groups)


def test_drs_filename():
    ds = xr.open_dataset(
        test_data / "bccaqv2_subset_sample/tasmax_bcc-csm1-1_subset.nc"
    )
    filename = drs_filename(ds)
    assert filename == "tasmax_bcc-csm1-1_historical+rcp85_r1i1p1_19500101-19500410.nc"


def test_drs_filename_unknown_project():
    ds = xr.open_dataset(
        test_data / "bccaqv2_subset_sample/tasmax_bcc-csm1-1_subset.nc"
    )
    ds.attrs["project_id"] = "unknown"
    filename = drs_filename(ds)
    assert filename == "tasmax_day_bcc-csm1-1_historical+rcp85_19500101-19500410.nc"


def test_drs_filename_cordex():
    ds = xr.open_dataset(test_data / "cordex_subset.nc")
    filename = drs_filename(ds)
    expected = "tasmin_NAM-44_MPI-M-MPI-ESM-MR_rcp85_r1i1p1_UQAM-CRCM5_v1_day_20960101-20960409.nc"
    assert filename == expected


def test_bccaqv2file():
    filename = "tasmin_day_BCCAQv2+ANUSPLIN300_inmcm4_historical+rcp85_r1i1p1_19500101-21001231.nc"
    file = ensemble_utils.Bccaqv2File.from_filename(filename)
    expected = ensemble_utils.Bccaqv2File(
        variable="tasmin",
        frequency="day",
        driving_model_id="inmcm4",
        driving_experiment_id="historical+rcp85",
        driving_realization="1",
        driving_initialization_method="1",
        driving_physics_version="1",
        date_start="19500101",
        date_end="21001231",
    )
    assert expected == file


@pytest.mark.parametrize(
    "filename,variable,rcp,models,expected",
    [
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_canesm2_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp85",
            None,
            True,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_canesm2_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp85",
            [ALL_24_MODELS],
            True,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_canesm2_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmax",
            "rcp85",
            [ALL_24_MODELS],
            False,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_canesm2_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp45",
            [ALL_24_MODELS],
            False,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_canesm2_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp85",
            ["HadGEM2-ES"],
            False,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_HadGEM2-ES_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp85",
            ["HadGEM2-ES"],
            True,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_MPI-ESM-LR_historical+rcp85_r3i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp85",
            [PCIC_12],
            True,
        ),
        (
            "tasmin_day_BCCAQv2+ANUSPLIN300_MPI-ESM-LR_historical+rcp85_r1i1p1_19500101-21001231.nc",
            "tasmin",
            "rcp85",
            [PCIC_12],
            False,
        ),
        ("tasmin_not_proper_filename.nc", "tasmin", None, None, False),
    ],
)
def test_bccaqv2_filter(filename, variable, rcp, models, expected):
    method = ensemble_utils.ParsingMethod.filename
    url = None
    variables = [variable]

    result = ensemble_utils._bccaqv2_filter(
        method=method,
        filename=filename,
        url=url,
        variables=variables,
        rcp=rcp,
        models=models,
    )
    assert result == expected
