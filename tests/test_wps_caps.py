import pywps.configuration

import finch.processes.utils
from _common import CFG_FILE, client_for
from finch.processes import get_indicators, get_processes, not_implemented
from finch.processes.utils import get_virtual_modules
from finch.wsgi import create_app


def test_wps_caps(client):
    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")

    # List of process identifiers returned by server
    names = resp.xpath_text(
        "/wps:Capabilities/wps:ProcessOfferings/wps:Process/ows:Identifier"
    ).split()

    # List of expected process names
    pnames = [p.identifier for p in get_processes()]

    # Sort
    pnames.sort()
    names.sort()

    assert set(names) == set(pnames)
    assert len(names) == len(pnames)


def test_wps_caps_no_datasets(client, monkeypatch):
    """Check that when no default dataset is configured, we get a lot less indicators."""

    def mock_config_get(*args, **kwargs):
        if args[:2] == ("finch", "datasets_config"):
            return ""
        return old_get_config_value(*args, **kwargs)

    old_get_config_value = pywps.configuration.get_config_value
    monkeypatch.setattr(finch.processes.utils, "get_config_value", mock_config_get)

    client = client_for(create_app(cfgfiles=CFG_FILE))

    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities/wps:ProcessOfferings/wps:Process/ows:Identifier"
    ).split()

    indicators = get_indicators(
        realms=["atmos", "land", "seaIce"], exclude=not_implemented
    )
    mod_dict = get_virtual_modules()
    for mod in mod_dict.keys():
        indicators.extend(mod_dict[mod]["indicators"])
    subset_processes_count = 4
    sdba_processes_count = 1
    others = 2
    assert len(
        indicators
    ) + others + subset_processes_count + sdba_processes_count == len(names)
