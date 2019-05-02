from unittest import mock

import pytest
from pathlib import Path

from tests.utils import wps_literal_input, execute_process
from finch.processes.wps_xsubset_bccaqv2 import SubsetBCCAQV2Process


@mock.patch("finch.processes.wps_xsubset_bccaqv2.get_opendap_datasets")
@mock.patch.object(SubsetBCCAQV2Process, "subset")
def test_bccaqv2_subset(mock_bccaq_subset, mock_datasets, client):
    identifier = "subset_ensemble_BCCAQv2"
    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
    ]

    metalink = mock.MagicMock()
    metalink.files = []

    mock_datasets.return_value = ["dataset1", "dataset2"]
    mock_bccaq_subset.return_value = metalink

    outputs = execute_process(client, identifier, inputs, output_names=["zip"])

    output_file = outputs[0]
    assert len(outputs) == 1
    assert output_file.endswith("zip")
    assert Path(output_file).exists()

    assert len(mock_bccaq_subset.call_args[0][0]["resource"]) == 2


@pytest.mark.online
def test_bccaqv2_subset_online(client):
    identifier = "subset_ensemble_BCCAQv2"
    up_right = 45.507485, -73.541295
    bottom_left = 45.385644, -73.691963

    inputs = [
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("rcp", "rcp26"),
        wps_literal_input("lon0", str(bottom_left[1])),
        wps_literal_input("lon1", str(up_right[1])),
        wps_literal_input("lat0", str(bottom_left[0])),
        wps_literal_input("lat1", str(up_right[0])),
        wps_literal_input("y0", "2010"),
        wps_literal_input("y1", "2010"),
    ]

    outputs = execute_process(client, identifier, inputs, output_names=["zip"])

    print(outputs)
