from finch.wsgi import create_app
import pywps.configuration
import pytest

import finch.processes
from finch.processes import indicators, get_processes
from .common import client_for, CFG_FILE


def test_wps_caps(client):
    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities/wps:ProcessOfferings/wps:Process/ows:Identifier"
    )

    assert len(get_processes()) == len(names.split())


@pytest.fixture
def monkeypatch_config(request):
    previous = pywps.configuration.CONFIG.get("finch", "dataset_bccaqv2")
    pywps.configuration.CONFIG.set("finch", "dataset_bccaqv2", "")
    request.addfinalizer(
        lambda: pywps.configuration.CONFIG.set("finch", "dataset_bccaqv2", previous)
    )


def test_wps_caps_no_datasets(client, monkeypatch):
    def mock_config_get(*args, **kwargs):
        if args[:2] == ("finch", "dataset_bccaqv2"):
            return ""
        return old_get_config_value(*args, **kwargs)

    old_get_config_value = pywps.configuration.get_config_value
    monkeypatch.setattr(finch.processes, "get_config_value", mock_config_get)

    client = client_for(create_app(cfgfiles=CFG_FILE))

    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities/wps:ProcessOfferings/wps:Process/ows:Identifier"
    )

    assert len(indicators) + 2 == len(names.split())
