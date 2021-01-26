from pywps import Service
from .common import client_for
from finch.processes import get_processes
import pytest




class TestClient:
    URL = "http://localhost:9099"

    @classmethod
    def setup_class(self):
        client = client_for(Service(processes=get_processes()))
        self.cap = client.get(service='wps', request='getcapabilities', version='1.0.0').data
        self.desc = client.get(service='wps', request='DescribeProcess', identifier="all", version='1.0.0').data

    def test_owslib(self):
        """Check that owslib can parse the processes' description."""
        from owslib.wps import WebProcessingService
        wps = WebProcessingService(self.URL, skip_caps=True)
        wps.getcapabilities(xml=self.cap)
        wps.describeprocess("all", xml=self.desc)

    def test_birdy(self):
        pytest.importorskip("birdy")
        from birdy import WPSClient
        WPSClient(url=self.URL, caps_xml=self.cap, desc_xml=self.desc)

