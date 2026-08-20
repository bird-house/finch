# noqa: D100
from pathlib import Path

import lxml.etree
from pywps import get_ElementMakerForVersion
from pywps.app.basic import get_xpath_ns
from pywps.tests import WpsClient, WpsTestResponse

VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)
xpath_ns = get_xpath_ns(VERSION)

TESTS_HOME = Path(__file__).parent
CFG_FILE = str(TESTS_HOME / "test.cfg")


class WpsTestClient(WpsClient):  # noqa: D101
    def get(self, *args, **kwargs):  # noqa: D102
        query = "?"
        for key, value in kwargs.items():
            query += f"{key}={value}&"
        return super().get(query)


def client_for(service):  # noqa: D103
    return WpsTestClient(service, WpsTestResponse)


def get_output(doc):  # noqa: D103
    # Copied from pywps/tests/test_execute.py.
    # TODO: make this helper method public in pywps.
    output = {}
    for output_el in xpath_ns(
        doc, "/wps:ExecuteResponse" "/wps:ProcessOutputs/wps:Output"
    ):
        [identifier_el] = xpath_ns(output_el, "./ows:Identifier")

        lit_el = xpath_ns(output_el, "./wps:Data/wps:LiteralData")
        if lit_el:
            output[identifier_el.text] = lit_el[0].text

        ref_el = xpath_ns(output_el, "./wps:Reference")
        if ref_el:
            output[identifier_el.text] = ref_el[0].attrib["href"]

        data_el = xpath_ns(output_el, "./wps:Data/wps:ComplexData")
        if data_el:
            output[identifier_el.text] = data_el[0].text

    return output


def get_metalinks(doc: lxml.etree.Element):
    """Return a dictionary of metaurls found in metalink XML, keyed by their file name.

    Parameters
    ----------
    doc : lxml.etree.Element
        Metalink XML etree.
    """
    output = {}
    for child in doc.iterchildren():
        if child.tag == "{urn:ietf:params:xml:ns:metalink}file":
            url = child.find("{urn:ietf:params:xml:ns:metalink}metaurl")
            output[child.attrib["name"]] = url.text

    return output
