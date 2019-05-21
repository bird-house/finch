from unittest import mock

import pytest
from pathlib import Path

from finch.processes import BCCAQV2HeatWave
from tests.utils import wps_literal_input, execute_process


@mock.patch("finch.processes.utils.get_bccaqv2_opendap_datasets")
@mock.patch.object(BCCAQV2HeatWave, "subset")
@mock.patch.object(BCCAQV2HeatWave, "compute_indices")
def test_bccaqv2_heatwave(
    mock_compute_indices, mock_bccaq_subset, mock_datasets, client
):
    identifier = "BCCAQv2_heat_wave_frequency_gridpoint"
    inputs = [
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("lat", "2"),
        wps_literal_input("lon", "3"),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "YS"),
    ]

    metalink = mock.MagicMock()
    tmp = Path(__file__).parent / "tmp"
    tmp.mkdir(exist_ok=True)

    metalink_file = mock.MagicMock()
    metalink_file.file = tmp / "tasmin_some_file.nc"
    metalink_file.file.write_text("dummy data")
    metalink_file2 = mock.MagicMock()
    metalink_file2.file = tmp / "tasmax_some_file.nc"
    metalink_file2.file.write_text("dummy data")

    metalink.files = [metalink_file, metalink_file2]

    mock_datasets.return_value = ["dataset1", "dataset2"]
    mock_bccaq_subset.return_value = metalink

    def write_dummy_data(filename):
        Path(filename).write_text("dummy data")

    mock_computed = mock.MagicMock()
    mock_compute_indices.return_value = mock_computed
    mock_computed.to_netcdf.side_effect = write_dummy_data

    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    output_file = outputs[0]
    assert len(outputs) == 1
    assert output_file.endswith("zip")
    assert Path(output_file).exists()

    assert len(mock_bccaq_subset.call_args[0][0]["resource"]) == 4


@pytest.mark.online
def test_bccaqv2_heatwave_online(client):
    identifier = "BCCAQv2_heat_wave_frequency_gridpoint"
    up_right = 45.507485, -73.541295

    inputs = [
        wps_literal_input("output_format", "netcdf"),
        wps_literal_input("lat", str(up_right[0])),
        wps_literal_input("lon", str(up_right[1])),
        wps_literal_input("thresh_tasmin", "22.0 degC"),
        wps_literal_input("thresh_tasmax", "30 degC"),
        wps_literal_input("window", "3"),
        wps_literal_input("freq", "YS"),
    ]

    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    print(outputs)
