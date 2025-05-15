import zipfile
from collections import namedtuple
from pathlib import Path

import geojson
import numpy as np
import pytest
from pywps.app.exceptions import ProcessError
from xarray import open_dataset

from _utils import execute_process, wps_literal_input
from finch.processes import ensemble_utils

mock_filenames = [
    "tasmax_bcc-csm1-1_rcp45_subset.nc",
    "tasmax_inmcm4_rcp45_subset.nc",
    "tasmin_bcc-csm1-1_rcp45_subset.nc",
    "tasmin_inmcm4_rcp45_subset.nc",
]

poly = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        # subsets bounds: -73.46, -72.54, 45.54, 46.46
        "coordinates": [
            [[-73.5, 45.58], [-72.5, 46.5], [-72.5, 45.58], [-73.5, 45.58]]
        ],
    },
}


def test_ensemble_hxmax_days_above_grid_point(client):
    # --- given ---
    identifier = "ensemble_grid_point_hxmax_days_above"
    inputs = [
        wps_literal_input("lat", "45.5"),
        wps_literal_input("lon", "-73.0"),
        wps_literal_input("scenario", "ssp245"),
        wps_literal_input("scenario", "ssp585"),
        wps_literal_input("dataset", "test_humidex"),
        wps_literal_input("threshold", "30"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    assert Path(outputs[0]).stem.startswith("testens_45_500_73_000_ssp245_ssp585")
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 12,  # there are roughly 4 months in the test datasets
        "scenario": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"hxmax_days_above_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        assert variable_dims == {"region": 1, "time": 12, "scenario": 2}

    assert len(ds.attrs["source_datasets"].split("\n")) == 19


def test_ensemble_spatial_avg_grid_point(client):
    # --- given ---
    identifier = "ensemble_grid_point_tg_mean"
    inputs = [
        wps_literal_input("lat", "45.5, 46"),
        wps_literal_input("lon", "-73.0, -73.3"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    # assert Path(outputs[0]).stem.startswith("testens_45_500_73_000_ssp245_ssp585")
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 2,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [f"tg_mean_p{p}" for p in (20, 50, 80)]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        for d, v in {"region": 2, "time": 4, "scenario": 2}.items():
            assert variable_dims[d] == v

    # --- given ---
    inputs.append(wps_literal_input("average", "True"))

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1

    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [f"tg_mean_p{p}" for p in (20, 50, 80)]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        for d, v in {"time": 4, "scenario": 2}.items():
            assert variable_dims[d] == v


def test_ensemble_temporal_avg_fail(client):

    with pytest.raises(
        ProcessError,
        match="NoApplicableCode: Process error: Finch failed with input dataset has insufficient number of years to apply temporal averaging",
    ):
        # --- given ---
        identifier = "ensemble_bbox_tn_mean"
        inputs = [
            wps_literal_input("lat0", "45.0"),
            wps_literal_input("lat1", "46.2"),
            wps_literal_input("lon0", "-75.0"),
            wps_literal_input("lon1", "-74.0"),
            wps_literal_input("start_date", "1970"),
            wps_literal_input("end_date", "1996"),
            wps_literal_input("scenario", "ssp370"),
            wps_literal_input("scenario", "ssp245"),
            wps_literal_input("dataset", "test_temp_avg"),
            wps_literal_input("freq", "MS"),
            wps_literal_input("ensemble_percentiles", ""),
            wps_literal_input("output_format", "netcdf"),
            wps_literal_input("output_name", "testens"),
            wps_literal_input("temporal_average", "True"),
            wps_literal_input("output_format", "csv"),
        ]

        # --- when ---
        outputs = execute_process(client, identifier, inputs)
        print(outputs)


def test_ensemble_temporal_avg_bbox_csv(client):
    # --- given ---
    identifier = "ensemble_bbox_tn_mean"
    inputs = [
        wps_literal_input("lat0", "45.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-75.0"),
        wps_literal_input("lon1", "-74.0"),
        wps_literal_input("scenario", "ssp370"),
        wps_literal_input("scenario", "ssp245"),
        wps_literal_input("dataset", "test_temp_avg"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", ""),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
        wps_literal_input("temporal_average", "True"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("time,horizon,lat,lon,scenario")
    assert all([line.startswith("tn_mean") for line in lines[0].split(",")[5:]])


def test_ensemble_temporal_avg_bbox(client):
    # --- given ---
    identifier = "ensemble_bbox_tn_mean"
    inputs = [
        wps_literal_input("lat0", "45.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-75.0"),
        wps_literal_input("lon1", "-74.0"),
        wps_literal_input("scenario", "ssp370"),
        wps_literal_input("scenario", "ssp245"),
        wps_literal_input("dataset", "test_temp_avg"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", ""),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
        wps_literal_input("temporal_average", "True"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1

    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {"time": 36, "scenario": 2, "realization": 3, "lat": 12, "lon": 12}

    ensemble_variables = [
        "tn_mean",
        "tn_mean_delta_1971_2000",
        "tn_mean_delta_1981_2010",
        "tn_mean_delta_1991_2020",
    ]
    assert sorted(ensemble_variables) == sorted([v for v in ds.data_vars])
    test_vals = dict()
    test_vals["ssp245"] = {
        "tn_mean": np.array([273.98428, 273.98315, 274.00925], dtype="float32"),
        "tn_mean_delta_1971_2000": np.array(
            [0.20800494, 0.4312828, 0.3815376], dtype="float32"
        ),
        "tn_mean_delta_1981_2010": np.array(
            [0.08352391, 0.0919781, 0.03475031], dtype="float32"
        ),
        "tn_mean_delta_1991_2020": np.array(
            [-0.29152888, -0.52326095, -0.41628787], dtype="float32"
        ),
    }
    test_vals["ssp370"] = {
        "tn_mean": np.array([274.01407, 273.97318, 274.01627], dtype="float32"),
        "tn_mean_delta_1971_2000": np.array(
            [0.23532315, 0.4178526, 0.3895025], dtype="float32"
        ),
        "tn_mean_delta_1981_2010": np.array(
            [0.11405201, 0.08232197, 0.04127601], dtype="float32"
        ),
        "tn_mean_delta_1991_2020": np.array(
            [-0.34937513, -0.50017464, -0.4307785], dtype="float32"
        ),
    }
    #
    for scen in test_vals.keys():
        for vv in ds.data_vars:
            test = ds[vv].sel(scenario=scen).squeeze()  #
            test = test.mean(dim=[d for d in test.dims if d != "realization"]).values
            np.testing.assert_array_equal(test.sort(), test_vals[scen][vv].sort())


def test_ensemble_spatial_avg_poly(client):
    # --- given ---
    identifier = "ensemble_polygon_tg_mean"
    inputs = [
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
        wps_literal_input("average", "True"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1

    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [f"tg_mean_p{p}" for p in (20, 50, 80)]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        for d, v in {"time": 4, "scenario": 2}.items():
            assert variable_dims[d] == v


def test_ensemble_spatial_avg_poly_noperc(client):
    # --- given ---
    identifier = "ensemble_polygon_tg_mean"
    inputs = [
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", ""),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
        wps_literal_input("average", "True"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1

    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    exp_dims = {
        "realization": 2,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 2,
    }
    assert dims == exp_dims

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == ["tg_mean"]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        for d, v in exp_dims.items():
            assert variable_dims[d] == v


def test_ensemble_heatwave_frequency_grid_point(client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    assert Path(outputs[0]).stem.startswith("testens_46_000_72_800_rcp45")
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 1,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        assert variable_dims == {"region": 1, "time": 4, "scenario": 1}

    assert len(ds.attrs["source_datasets"].split("\n")) == 4


def test_ensemble_tx_mean_grid_point_no_perc_csv(client):
    # --- given ---
    identifier = "ensemble_grid_point_tx_mean"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", ""),
        wps_literal_input("output_format", "csv"),
        wps_literal_input("output_name", "testens"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("time,lat,lon,scenario")
    assert len(lines[0].split(",")) == 6
    assert all([line.startswith("tx_mean:") for line in lines[0].split(",")[-2:]])
    n_data_rows = len(lines) - 2
    assert n_data_rows == 4  # lat=1, lon=1, time=4 (last month


def test_ensemble_heatwave_frequency_grid_point_no_perc(client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", ""),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    assert Path(outputs[0]).stem.startswith("testens_46_000_72_800_rcp45")
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 1,
        "realization": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == ["heat_wave_frequency"]
    for var in ensemble_variables.values():
        variable_dims = {d: s for d, s in zip(var.dims, var.shape)}
        assert variable_dims == {
            "region": 1,
            "time": 4,
            "scenario": 1,
            "realization": 2,
        }

    assert len(ds.attrs["source_datasets"].split("\n")) == 4


def test_ensemble_dded_grid_point_multiscenario(client):
    # --- given ---
    identifier = "ensemble_grid_point_degree_days_exceedance_date"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh", "-5 degC"),
        wps_literal_input("sum_thresh", "30 K days"),
        wps_literal_input("op", ">"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"degree_days_exceedance_date_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 4, "scenario": 2}


def test_ensemble_dded_grid_point_multiscenario_noperc(client):
    # --- given ---
    identifier = "ensemble_grid_point_degree_days_exceedance_date"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("scenario", "rcp45"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh", "-5 degC"),
        wps_literal_input("sum_thresh", "30 K days"),
        wps_literal_input("op", ">"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", ""),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "region": 1,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 2,
        "realization": 2,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == ["degree_days_exceedance_date"]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {
            "region": 1,
            "time": 4,
            "scenario": 2,
            "realization": 2,
        }


def test_ensemble_heatwave_frequency_bbox(client):
    # --- given ---
    identifier = "ensemble_bbox_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-73.0"),
        wps_literal_input("lon1", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "lat": 2,
        "lon": 2,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 1,
    }

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"time": 4, "lat": 2, "lon": 2, "scenario": 1}

    inputs.append(wps_literal_input("average", "True"))
    outputs = execute_process(client, identifier, inputs)

    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {"time": 4, "scenario": 1}  # Spatial average has been taken.

    ensemble_variables = {k: v for k, v in ds.data_vars.items()}
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"time": 4, "scenario": 1}


def test_ensemble_heatwave_frequency_grid_point_csv(client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("time,lat,lon,scenario")
    n_data_rows = len(lines) - 2
    assert n_data_rows == 4  # time=4 (last month is NaN, but kept in CSV)


def test_ensemble_heatwave_frequency_bbox_csv(client):
    # --- given ---
    identifier = "ensemble_bbox_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat0", "46.0"),
        wps_literal_input("lat1", "46.2"),
        wps_literal_input("lon0", "-73.0"),
        wps_literal_input("lon1", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("time,lat,lon")
    n_data_rows = len(lines) - 2
    assert (
        n_data_rows == 2 * 2 * 4
    )  # lat=2, lon=2, time=4 (last month is NaN, but kept in CSV)


def test_ensemble_heatwave_frequency_grid_point_dates(client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("start_date", "1950"),
        wps_literal_input("end_date", "1950-03-31"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {"region": 1, "time": 3, "scenario": 1}

    ensemble_variables = dict(ds.data_vars)

    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (10, 50, 90)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 3, "scenario": 1}


def test_ensemble_heatwave_frequency_grid_point_models(client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_single_cell"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("models", "CSIRO-Mk3-6-0"),
        wps_literal_input("models", "HadGEM2-ES"),
        wps_literal_input("models", "MRI-CGCM3"),
        wps_literal_input("output_format", "netcdf"),
    ]

    execute_process(client, identifier, inputs)


def test_ensemble_heatwave_frequency_grid_point_models_pcic(client):
    # --- given ---
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_single_cell"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("models", "pcic12"),
        wps_literal_input("output_format", "netcdf"),
    ]
    execute_process(client, identifier, inputs)


def test_compute_intermediate_variables(monkeypatch):
    # --- given ---
    workdir = Path(__file__).parent / "tmp" / "temp_compute_intermediate_variables"
    workdir.mkdir(parents=True, exist_ok=True)
    subset_folder = Path(__file__).parent / "data" / "bccaqv2_subset_sample"
    mock_paths = [subset_folder / p for p in mock_filenames]

    required_variables = ["tasmin_per"]
    literal_input = namedtuple("LiteralInput", ["data", "identifier"])
    # --- when ---
    files_outputs = ensemble_utils.compute_intermediate_variables(
        mock_paths,
        {"tasmin", "tasmax"},
        required_variables,
        workdir,
        {"perc_tasmin": [literal_input(10, "perc_tasmin")]},
    )

    # --- then ---
    datasets = [
        "bcc-csm1-1_rcp45_subset.nc",
        "inmcm4_rcp45_subset.nc",
    ]
    expected = [
        workdir / f"{v}_{dataset}" for v in required_variables for dataset in datasets
    ]

    assert sorted(files_outputs) == sorted(expected)


def test_ensemble_compute_intermediate_cold_spell_duration_index_grid_point(client):
    # --- given ---
    identifier = "ensemble_grid_point_cold_spell_duration_index"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("window", "6"),
        wps_literal_input("freq", "YS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("perc_tasmin", "10"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {"region": 1, "time": 1, "scenario": 1}

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [f"csdi_6_p{p}" for p in (20, 50, 80)]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 1, "scenario": 1}


def test_ensemble_compute_intermediate_growing_degree_days_grid_point(client):
    # --- given ---
    identifier = "ensemble_grid_point_growing_degree_days"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {"region": 1, "time": 1, "scenario": 1}

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [
        f"growing_degree_days_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"region": 1, "time": 1, "scenario": 1}

    inputs.append(wps_literal_input("average", "True"))

    # --- when ---
    outputs = execute_process(client, identifier, inputs)


def test_ensemble_heatwave_frequency_polygon(client):
    # --- given ---
    identifier = "ensemble_polygon_heat_wave_frequency"
    inputs = [
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {
        "lat": 11,
        "lon": 11,
        "time": 4,  # there are roughly 4 months in the test datasets
        "scenario": 1,
    }
    data = ds["heat_wave_frequency_p20"].isel(scenario=0, time=1).data
    assert np.isnan(data).sum() == 55
    assert (~np.isnan(data)).sum() == 66

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"lat": 11, "lon": 11, "time": 4, "scenario": 1}

    inputs.append(wps_literal_input("average", "True"))
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    ds = open_dataset(outputs[0])
    dims = dict(ds.dims)
    assert dims == {"time": 4, "scenario": 1}

    ensemble_variables = dict(ds.data_vars)
    assert sorted(ensemble_variables) == [
        f"heat_wave_frequency_p{p}" for p in (20, 50, 80)
    ]
    for var in ensemble_variables.values():
        variable_dims = dict(zip(var.dims, var.shape))
        assert variable_dims == {"time": 4, "scenario": 1}


def test_ensemble_heatwave_frequency_polygon_csv(client):
    # --- given ---
    identifier = "ensemble_polygon_heat_wave_frequency"
    inputs = [
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("scenario", "rcp26"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "csv"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("time,lat,lon")
    n_data_rows = len(lines) - 2  # header + ending line
    # lat: 11 lon: 11, time=4 (last month is NaN, but kept in CSV)
    assert n_data_rows == 11 * 11 * 4

    # --- given ---
    inputs.append(wps_literal_input("average", "True"))

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    assert len(outputs) == 1
    zf = zipfile.ZipFile(outputs[0])
    assert len(zf.namelist()) == 2  # metadata + data
    data_filename = [n for n in zf.namelist() if "metadata" not in n]
    csv = zf.read(data_filename[0]).decode()
    lines = csv.split("\n")
    assert lines[0].startswith("time")
    n_data_rows = len(lines) - 2  # header + ending line
    # after spatial average, time=4 (last month is NaN, but kept in CSV)
    assert n_data_rows == 4


def test_ensemble_invalid_parameters(client):
    identifier = "ensemble_grid_point_heat_wave_frequency"
    inputs = [
        wps_literal_input("lat", "46"),
        wps_literal_input("lon", "-72.8"),
        wps_literal_input("scenario", "rcp85"),
        wps_literal_input("dataset", "test_subset"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "MS"),
        wps_literal_input("ensemble_percentiles", "20, 50, 80"),
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("output_name", "testens"),
    ]

    # --- when ---
    # scenario not in this dataset
    with pytest.raises(ProcessError, match="InvalidParameterValue"):
        execute_process(client, identifier, inputs)

    inputs[2] = wps_literal_input("scenario", "rcp45")
    inputs.append(wps_literal_input("models", "MIROC5"))  # model not in this dataset
    with pytest.raises(ProcessError, match="InvalidParameterValue"):
        execute_process(client, identifier, inputs)

    inputs.pop(-1)
    identifier = "ensemble_grid_point_cwd"  # dataset doesnt have PR
    with pytest.raises(ProcessError, match="InvalidParameterValue"):
        execute_process(client, identifier, inputs)
