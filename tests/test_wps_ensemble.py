from pathlib import Path
from unittest import mock
import zipfile

import numpy as np
import geojson
from xarray import open_dataset
import pytest

from finch.processes import ensemble_utils
from finch.processes.constants import PCIC_12
from tests.utils import execute_process, mock_local_datasets, wps_literal_input

mock_filenames = [
    "tasmax_bcc-csm1-1_subset.nc",
    "tasmax_inmcm4_subset.nc",
    "tasmin_bcc-csm1-1_subset.nc",
    "tasmin_inmcm4_subset.nc",
]

poly = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        # subsets bounds: -73.46, -72.54, 45.54, 46.46
        "coordinates": [[[-73.5, 45.58], [-72.5, 46.5], [-72.5, 45.58]]],
    },
}


@pytest.fixture
def mock_datasets(monkeypatch):
    mock_local_datasets(monkeypatch, filenames=mock_filenames)


def test_ensemble_heatwave_frequency_grid_point(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 4,  # there are roughly 4 months in the test datasets
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        assert variable_dims == {"region": 1, "time": 4}

    assert len(ds.attrs['source_datasets'].split('\n')) == 4


def test_ensemble_heatwave_frequency_bbox(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_bbox_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-73.0"),
        wps_literal_input("lon1", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "lat": 2,
        "lon": 2,
        "time": 4,  # there are roughly 4 months in the test datasets
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"time": 4, "lat": 2, "lon": 2}


def test_ensemble_heatwave_frequency_grid_point_csv(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("lat,lon,time")
    n_data_rows = len(lines) - 2
    assert n_data_rows == 3  # time=3 (last month is NaN)


def test_ensemble_heatwave_frequency_bbox_csv(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_bbox_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-73.0"),
        wps_literal_input("lon1", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("lat,lon,time")
    n_data_rows = len(lines) - 2
    assert n_data_rows == 2 * 2 * 3  # lat=2, lon=2, time=3 (last month is NaN)


def test_ensemble_heatwave_frequency_grid_point_dates(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("start_date", "1950"),
        wps_literal_input("end_date", "1950-03-31"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 3,
    }

    ensemble_variables = dict(ds.data_vars)

    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (10, 50, 90)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 3}


def test_ensemble_heatwave_frequency_grid_point_models(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("models", "CSIRO-Mk3-6-0"),
        wps_literal_input("models", "HadGEM2-ES"),
        wps_literal_input("models", "MRI-CGCM3"),
        wps_literal_input("output_format", "netcdf"),
    ]
    from pywps.configuration import CONFIG

    CONFIG.set("finch", "dataset_bccaqv2", "/mock_local/path")
    subset_sample = Path(__file__).parent / "data" / "bccaqv2_subset_sample"

    # --- when ---
    with mock.patch(
        "finch.processes.ensemble_utils.get_bccaqv2_local_files_datasets"
    ) as mock_datasets:
        mock_datasets.return_value = [str(subset_sample / f) for f in mock_filenames]
        execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert mock_datasets.call_args[1]["models"] == [
        "CSIRO-Mk3-6-0",
        "HadGEM2-ES",
        "MRI-CGCM3",
    ]


def test_ensemble_heatwave_frequency_grid_point_models_pcic(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("models", PCIC_12),
        wps_literal_input("output_format", "netcdf"),
    ]
    from pywps.configuration import CONFIG

    CONFIG.set("finch", "dataset_bccaqv2", "/mock_local/path")
    subset_sample = Path(__file__).parent / "data" / "bccaqv2_subset_sample"

    # --- when ---
    with mock.patch(
        "finch.processes.ensemble_utils.get_bccaqv2_local_files_datasets"
    ) as mock_datasets:
        mock_datasets.return_value = [str(subset_sample / f) for f in mock_filenames]
        execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert mock_datasets.call_args[1]["models"] == [PCIC_12]


def test_compute_intermediate_variables(monkeypatch):
    # --- given ---
    workdir = Path(__file__).parent / "tmp" / "temp_compute_intermediate_variables"
    workdir.mkdir(parents=True, exist_ok=True)
    subset_folder = Path(__file__).parent / "data" / "bccaqv2_subset_sample"
    mock_paths = [subset_folder / p for p in mock_filenames]

    required_variables = ["tn10"]

    # --- when ---
    files_outputs = ensemble_utils.compute_intermediate_variables(
        mock_paths, required_variables, workdir
    )

    # --- then ---
    datasets = [
        "bcc-csm1-1_subset.nc",
        "inmcm4_subset.nc",
    ]
    expected = [
        workdir / f"{v}_{dataset}" for v in required_variables for dataset in datasets
    ]

    assert sorted(files_outputs) == sorted(expected)


def test_ensemble_compute_intermediate_cold_spell_duration_index_grid_point(
    mock_datasets, client
):
    # --- given ---
    identifier = "ensemble_grid_point_cold_spell_duration_index"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("window", "6"),
        wps_literal_input("freq", "YS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 1,
    }

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [f"csdi_6_p{p}" for p in (20, 50, 80)]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 1}


def test_ensemble_compute_intermediate_growing_degree_days_grid_point(
    mock_datasets, client
):
    # --- given ---
    identifier = "ensemble_grid_point_growing_degree_days"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 1,
    }

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [
        f"growing_degree_days_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 1}


def test_ensemble_heatwave_frequency_polygon(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_polygon_heat_wave_frequency"
    inputs = [
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "lat": 11,
        "lon": 11,
        "time": 4,  # there are roughly 4 months in the test datasets
    }
    data = ds["heat_wave_frequency_p20"][1, :].data
    assert np.isnan(data).sum() == 55
    assert (~np.isnan(data)).sum() == 66

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"lat": 11, "lon": 11, "time": 4}


def test_ensemble_heatwave_frequency_polygon_csv(mock_datasets, client):
    # --- given ---
    identifier = "ensemble_polygon_heat_wave_frequency"
    inputs = [
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("lat,lon,time")
    n_data_rows = len(lines) - 2  # header + ending line
    # lat-lon=66 (not NaN), time=3 (last month is NaN)
    assert n_data_rows == 66 * 3
