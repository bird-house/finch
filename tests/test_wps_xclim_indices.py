from inspect import signature
import json
import pytest
from lxml import etree
import numpy as np
import xarray as xr
import pandas as pd

import finch
import finch.processes
from finch.processes.wps_xclim_indices import XclimIndicatorBase
from finch.processes.wps_base import make_xclim_indicator_process
from . utils import execute_process, wps_input_file, wps_literal_input
from pathlib import Path
from pywps.app.exceptions import ProcessError
from pywps import configuration
from unittest import mock
from numpy.testing import assert_equal
from xclim.testing import open_dataset


K2C = 273.16
configuration.CONFIG['finch:metadata']['testing_session'] = "True"


def _get_output_standard_name(process_identifier):
    for p in finch.processes.get_processes():
        if p.identifier == process_identifier:
            return p.xci.standard_name


@pytest.mark.parametrize("indicator", finch.processes.indicators)
def test_indicators_processes_discovery(indicator):
    process = make_xclim_indicator_process(indicator, "Process", XclimIndicatorBase)
    assert indicator.identifier == process.identifier
    sig = signature(indicator.compute)
    # the phase parameter is set by a partial function in xclim, so there is
    # no input necessary from the user in the WPS process
    parameters = set([k for k in sig.parameters.keys() if k != "phase"])
    parameters.add("check_missing")
    parameters.add("missing_options")
    parameters.add("cf_compliance")
    parameters.add("data_validation")
    parameters.add("variable")
    if "indexer" in parameters:
        parameters.remove("indexer")
        parameters.add("month")
        parameters.add("season")

    assert_equal(parameters, set(i.identifier for i in process.inputs), indicator.identifier)


# TODO : Extend test coverage
def test_processes(client, netcdf_datasets):
    """Run a dummy calculation for every process, keeping some default parameters."""
    # indicators = finch.processes.indicators
    processes = filter(lambda x: isinstance(x, XclimIndicatorBase), finch.processes.xclim.__dict__.values())
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
                raise NotImplementedError
        outputs = execute_process(client, process.identifier, inputs)
        ds = xr.open_dataset(outputs[0])
        output_variable = list(ds.data_vars)[0]

        assert getattr(ds, output_variable).standard_name == process.xci.standard_name
        assert ds.attrs['testing_session']

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
            client, identifier, inputs, output_names=["output_netcdf", "ref"]
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
        execute_process(
            client, identifier, inputs, output_names=["output_netcdf", "ref"]
        )


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
        wps_literal_input("missing_options", json.dumps({"pct": {"tolerance": 0.1}}))
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.tg_mean.isnull(), False)


def test_stats_process(client, netcdf_datasets):
    """Test stats and the capacity to choose the variable."""
    identifier = "stats"

    inputs = [
        wps_input_file("da", netcdf_datasets["pr_discharge"]),
        wps_literal_input("freq", "YS"),
        wps_literal_input("op", "max"),
        wps_literal_input("season", "JJA"),
        wps_literal_input("variable", "discharge")
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.qsummermax.isnull(), False)


def test_freqanalysis_process(client, netcdf_datasets):
    identifier = "freq_analysis"
    inputs = [
        wps_input_file("da", netcdf_datasets["discharge"]),
        wps_literal_input("t", "2"),
        wps_literal_input("t", "50"),
        wps_literal_input("freq", "YS"),
        wps_literal_input("mode", "max"),
        wps_literal_input("season", "JJA"),
        wps_literal_input("dist", "gumbel_r"),
        wps_literal_input("variable", "discharge")
    ]
    outputs = execute_process(client, identifier, inputs)
    ds = xr.open_dataset(outputs[0])
    np.testing.assert_array_equal(ds.q1maxsummer.shape, (2, 5, 6))


class TestFitProcess:
    identifier = "fit"

    def test_simple(self, client, netcdf_datasets):

        inputs = [
            wps_input_file("da", netcdf_datasets["discharge"]),
            wps_literal_input("dist", "norm"),
        ]
        outputs = execute_process(client, self.identifier, inputs)
        ds = xr.open_dataset(outputs[0])
        np.testing.assert_array_equal(ds.params.shape, (2, 5, 6))

    def test_nan(self, client, q_series, tmp_path):
        q_series([333, 145, 203, 109, 430, 230, np.nan]).to_netcdf(tmp_path / "q.nc")
        inputs = [
            wps_input_file("da", tmp_path / "q.nc"),
            wps_literal_input("dist", "norm"),
        ]
        outputs = execute_process(client, self.identifier, inputs)
        ds = xr.open_dataset(outputs[0])
        np.testing.assert_array_equal(ds.params.isnull(), False)


def test_rain_approximation(client, pr_series, tas_series, tmp_path):
    identifier = "prlp"

    pr_series(np.ones(10)).to_netcdf(tmp_path / 'pr.nc')
    tas_series(np.arange(10) + K2C).to_netcdf(tmp_path / 'tas.nc')

    inputs = [wps_input_file("pr", tmp_path / "pr.nc"),
              wps_input_file("tas", tmp_path / "tas.nc"),
              wps_literal_input("thresh", "5 degC"),
              wps_literal_input("method", "binary")]

    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        np.testing.assert_allclose(
            ds.prlp, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1], atol=1e-5, rtol=1e-3
        )


@pytest.mark.xfail
def test_two_nondefault_variable_name(client, pr_series, tas_series, tmp_path):
    identifier = "prlp"

    pr_series(np.ones(10)).to_dataset(name="my_pr").to_netcdf(tmp_path / 'pr.nc')
    tas_series(np.arange(10) + K2C).to_dataset(name="my_tas").to_netcdf(tmp_path / 'tas.nc')

    inputs = [wps_input_file("pr", tmp_path / "pr.nc"),
              wps_input_file("tas", tmp_path / "tas.nc"),
              wps_literal_input("thresh", "5 degC"),
              wps_literal_input("method", "binary"),
              wps_literal_input("variable", "my_pr")
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
    inputs = [wps_input_file("tas", tmp_path / "tas.nc"),
              wps_literal_input("thresh", "4 degC"),
              wps_literal_input("op", ">"),
              wps_literal_input("sum_thresh", "200 K days")
              ]

    outputs = execute_process(client, identifier, inputs)
    with xr.open_dataset(outputs[0]) as ds:
        np.testing.assert_array_equal(ds.degree_days_exceedance_date, np.array([[153, 136, 9, 6]]).T)
