from finch.processes.utils import get_bcca2v2_opendap_datasets
from finch.processes.wps_xsubset_bccaqv2 import SubsetBCCAQV2Process
import pytest


@pytest.mark.online
def test_get_opendap_datasets_bccaqv2():
    url = SubsetBCCAQV2Process.bccaqv2_link
    variable = "tasmin"
    rcp = "rcp26"

    urls = get_bcca2v2_opendap_datasets(url, variable, rcp)
    assert len(urls) == 27
