import json
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from lxml import etree
from numpy.testing import assert_equal
from pywps.app.exceptions import ProcessError
from xclim.testing import open_dataset
from xclim.testing.helpers import test_timeseries as timeseries

import finch
import finch.processes
from _utils import execute_process, wps_input_file, wps_literal_input
from finch.processes import get_indicators, not_implemented
from finch.processes.wps_base import make_xclim_indicator_process
from finch.processes.wps_xclim_indices import XclimIndicatorBase

K2C = 273.16


def _get_output_standard_name(process_identifier):
    for p in finch.processes.get_processes():
        if p.identifier == process_identifier:
            return p.xci.standard_name


@pytest.mark.parametrize(
    "indicator",
    get_indicators(realms=["atmos", "land", "seaIce"], exclude=not_implemented),
)
def test_indicators_processes_discovery(indicator):
    process = make_xclim_indicator_process(indicator, "Process", XclimIndicatorBase)
    assert indicator.identifier == process.identifier
    # Remove args not supported by finch: we remove special kinds,
    # 50 is "kwargs". 70 is Dataset ('ds') and 99 is "unknown". All normal types are 0-9.
    parameters = {
        k for k, v in indicator.parameters.items() if v["kind"] < 50 or k == "indexer"
    }
    parameters.add("check_missing")
    parameters.add("missing_options")
    parameters.add("cf_compliance")
    parameters.add("data_validation")
    parameters.add("variable")
    parameters.add("output_name")
    parameters.add("output_format")
    parameters.add("csv_precision")
    if "indexer" in parameters:
        parameters.remove("indexer")
        parameters.add("month")
        parameters.add("season")

    assert_equal(
        parameters, {i.identifier for i in process.inputs}, indicator.identifier
    )


# TODO : Extend test coverage
def test_processes(client, netcdf_datasets):
    """Run a dummy calculation for every process, keeping some default parameters."""
    # indicators = finch.processes.indicators
    processes = filter(
        lambda x: isinstance(x, XclimIndicatorBase),
        client.application.processes.values(),
    )
    literal_inputs = {
        "freq": "MS",
        "window": "3",
        "mid_date": "07-01",
        "before_date": "07-01",
    }
    keep_defaults = ["thresh", "thresh_tasmin", "thresh_tasmax"]

    attrs = xr.open_dataset(list(netcdf_datasets.values())[0], decode_times=False).attrs

    for process in processes:
        inputs = []
        for process_input in process.inputs:
            name = process_input.identifier
            if name in netcdf_datasets.keys():
                inputs.append(wps_input_file(name, netcdf_datasets[name]))
            elif name in literal_inputs.keys():
                inputs.append(wps_literal_input(name, literal_inputs[name]))
            elif name in keep_defaults:
                pass
            else:
                break
        else:
            outputs = execute_process(client, process.identifier, inputs)
            ds = xr.open_dataset(outputs[0])
            output_variable = list(ds.data_vars)[0]

            assert (
                getattr(ds, output_variable).standard_name == process.xci.standard_name
            )
            assert ds.attrs["testing_session"]

            model = attrs["driving_model_id"]
            experiment = attrs["driving_experiment_id"].replace(",", "+")
            ensemble = (
                f"r{attrs['driving_realization']}"
                f"i{attrs['driving_initialization_method']}"
                f"p{attrs['driving_physics_version']}"
            )
            date_start = pd.to_datetime(str(ds.time[0].values))
            date_end = pd.to_datetime(str(ds.time[-1].values))

            expected = (
                f"{output_variable.replace('_', '-')}_"
                f"{model}_{experiment}_{ensemble}_"
                f"{date_start:%Y%m%d}-{date_end:%Y%m%d}.nc"
            )
            assert Path(outputs[0]).name == expected


def test_wps_daily_temperature_range_multiple(client, netcdf_datasets):
    identifier = "dtr"
    inputs = [wps_literal_input("freq", "YS")]
    for _ in range(5):
        inputs.append(wps_input_file("tasmax", netcdf_datasets["tasmax"]))
        inputs.append(wps_input_file("tasmin", netcdf_datasets["tasmin"]))

    with mock.patch(
        "finch.processes.wps_xclim_indices.FinchProgressBar"
    ) as mock_progress:
        outputs = execute_process(
            client, identifier, inputs, output_names=["output", "ref"]
        )

    assert mock_progress.call_args_list[0][1]["start_percentage"] == 0
    assert mock_progress.call_args_list[0][1]["end_percentage"] == 20
    assert mock_progress.call_args_list[4][1]["start_percentage"] == 80
    assert mock_progress.call_args_list[4][1]["end_percentage"] == 100

    et = etree.fromstring(outputs[1].data[0].encode())
    urls = [e[2].text for e in et if e.tag.endswith("file")]

    assert len(urls) == 5, "Containing 10 files"
    assert len(set(urls)) == 5, "With different links"
    assert urls[1].endswith("-1.nc")


def test_wps_daily_temperature_range_multiple_not_same_length(client, netcdf_datasets):
    identifier = "dtr"
    inputs = [wps_literal_input("freq", "YS")]
    for _ in range(5):
        inputs.append(wps_input_file("tasmax", netcdf_datasets["tasmax"]))
        inputs.append(wps_input_file("tasmin", netcdf_datasets["tasmin"]))

    inputs.pop()

    with pytest.raises(ProcessError, match="must be equal"):
        execute_process(client, identifier, inputs, output_names=["output", "ref"])


def test_heat_wave_frequency_window_thresh_parameters(client, netcdf_datasets):
    identifier = "heat_wave_frequency"
    inputs = [
        wps_input_file("tasmax", netcdf_datasets["tasmax"]),
        wps_input_file("tasmin", netcdf_datasets["tasmin"]),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "YS"),
        wps_literal_input("thresh_tasmin", "20 degC"),
        wps_literal_input("thresh_tasmax", "25 degC"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds.attrs["frequency"] == "yr"
    assert ds.heat_wave_frequency.standard_name == _get_output_standard_name(identifier)


def test_heat_wave_index_thresh_parameter(client, netcdf_datasets):
    identifier = "heat_wave_index"
    inputs = [
        wps_input_file("tasmax", netcdf_datasets["tasmax"]),
        wps_literal_input("thresh", "30 degC"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])

    assert ds["heat_wave_index"].standard_name == _get_output_standard_name(identifier)


def test_missing_options(client, netcdf_datasets):
    identifier = "tg_mean"
    inputs = [
        wps_input_file("tas", netcdf_datasets["tas_missing"]),
        wps_literal_input("freq", "YS"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.tg_mean.isnull(), True)

    inputs = [
        wps_input_file("tas", netcdf_datasets["tas_missing"]),
        wps_literal_input("freq", "YS"),
        wps_literal_input("check_missing", "pct"),
        wps_literal_input("missing_options", json.dumps({"pct": {"tolerance": 0.1}})),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.tg_mean.isnull(), False)


def test_stats_process(client, netcdf_datasets):
    """Test stats and the capacity to choose the variable."""
    identifier = "discharge_stats"

    inputs = [
        wps_input_file("discharge", netcdf_datasets["pr_discharge"]),
        wps_literal_input("freq", "YS"),
        wps_literal_input("op", "max"),
        wps_literal_input("season", "JJA"),
        wps_literal_input("variable", "discharge"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.qsummermax.isnull(), False)


def test_freqanalysis_process(client, netcdf_datasets):
    identifier = "freq_analysis"
    inputs = [
        wps_input_file("discharge", netcdf_datasets["discharge"]),
        wps_literal_input("t", "2"),
        wps_literal_input("t", "50"),
        wps_literal_input("freq", "YS"),
        wps_literal_input("mode", "max"),
        wps_literal_input("season", "JJA"),
        wps_literal_input("dist", "gumbel_r"),
        wps_literal_input("variable", "discharge"),
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.q1maxsummer.shape, (2, 5, 6))


class TestFitProcess:
    identifier = "discharge_distribution_fit"

    def test_simple(self, client, netcdf_datasets):
        inputs = [
            wps_input_file("discharge", netcdf_datasets["discharge"]),
            wps_literal_input("dist", "norm"),
        ]
        outputs = execute_process(client, self.identifier, inputs)
        ds = xr.open_dataset(outputs[0])
        np.testing.assert_array_equal(ds.params.shape, (2, 5, 6))

    def test_nan(self, client, tmp_path):
        timeseries(
            values=[333, 145, 203, 109, 430, 230, np.nan], variable="q"
        ).to_netcdf(tmp_path / "q.nc")
        inputs = [
            wps_input_file("discharge", tmp_path / "q.nc"),
            wps_literal_input("dist", "norm"),
        ]
        outputs = execute_process(client, self.identifier, inputs)
        ds = xr.open_dataset(outputs[0])
        np.testing.assert_array_equal(ds.params.isnull(), False)


def test_rain_approximation(client, tmp_path):
    identifier = "prlp"
    timeseries(values=np.ones(10), variable="pr").to_netcdf(tmp_path / "pr.nc")
    timeseries(values=np.arange(10) + K2C, variable="tas").to_netcdf(
        tmp_path / "tas.nc"
    )
    inputs = [
        wps_input_file("pr", tmp_path / "pr.nc"),
        wps_input_file("tas", tmp_path / "tas.nc"),
        wps_literal_input("thresh", "5 degC"),
        wps_literal_input("method", "binary"),
    ]

    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        np.testing.assert_allclose(
            ds.prlp, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1], atol=1e-5, rtol=1e-3
        )


@pytest.mark.xfail
def test_two_nondefault_variable_name(client, tmp_path):
    identifier = "prlp"
    timeseries(values=np.ones(10), variable="pr").to_netcdf(tmp_path / "pr.nc")
    timeseries(values=np.arange(10) + K2C, variable="tas").to_netcdf(
        tmp_path / "tas.nc"
    )
    inputs = [
        wps_input_file("pr", tmp_path / "pr.nc"),
        wps_input_file("tas", tmp_path / "tas.nc"),
        wps_literal_input("thresh", "5 degC"),
        wps_literal_input("method", "binary"),
        wps_literal_input("variable", "my_pr"),
    ]
    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        np.testing.assert_allclose(
            ds.prlp, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1], atol=1e-5, rtol=1e-3
        )


def test_degree_days_exceedance_date(client, tmp_path):
    identifier = "degree_days_exceedance_date"

    tas = open_dataset("FWI/GFWED_sample_2017.nc").tas
    tas.attrs.update(
        cell_methods="time: mean within days", standard_name="air_temperature"
    )

    tas.to_netcdf(tmp_path / "tas.nc")
    inputs = [
        wps_input_file("tas", tmp_path / "tas.nc"),
        wps_literal_input("thresh", "4 degC"),
        wps_literal_input("op", ">"),
        wps_literal_input("sum_thresh", "200 K days"),
        wps_literal_input("output_format", "csv"),
        wps_literal_input("csv_precision", "-1"),
    ]

    outputs = execute_process(client, identifier, inputs)
    with ZipFile(outputs[0]) as thezip:
        with thezip.open("out.csv") as thefile:
            ds = pd.read_csv(thefile).to_xarray()
    np.testing.assert_array_equal(
        ds.degree_days_exceedance_date, np.array([10, 10, 140, 150])
    )


def test_hxmax_day_above(client, tmp_path):
    identifier = "hxmax_days_above"
    data = timeseries(values=[27, 18, 35, 40, 39, 20, 29, 29.5], variable="tasmax")
    data.attrs["units"] = ""
    data.name = "HXmax"
    data.to_netcdf(tmp_path / "hxmax.nc")
    # timeseries(values=np.arange(10) + K2C, variable='tas').to_netcdf(tmp_path / "tas.nc")
    inputs = [
        wps_input_file("HXmax", tmp_path / "hxmax.nc"),
        wps_literal_input("threshold", "30"),
        wps_literal_input("check_missing", "skip"),
    ]
    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0], decode_timedelta=False) as ds:
        np.testing.assert_array_equal(ds.hxmax_days_above.values, 3)
