from pywps import Service
from pywps.configuration import CONFIG
import pytest

from .common import client_for
from finch.processes import processes, indicators


def test_wps_caps():
    client = client_for(Service(processes=processes))
    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities/wps:ProcessOfferings/wps:Process/ows:Identifier"
    )

    assert len(processes) == len(names.split())


@pytest.fixture
def monkeypatch_config(request):
    previous = CONFIG.get("finch", "dataset_bccaqv2")
    CONFIG.set("finch", "dataset_bccaqv2", "")
    request.addfinalizer(lambda: CONFIG.set("finch", "dataset_bccaqv2", previous))


def test_wps_caps_no_datasets(monkeypatch_config):
    client = client_for(Service(processes=processes))
    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities/wps:ProcessOfferings/wps:Process/ows:Identifier"
    )

    assert len(indicators) + 2 == len(names.split())
