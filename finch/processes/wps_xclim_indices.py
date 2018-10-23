from pywps import Process
from pywps import ComplexInput, ComplexOutput, FORMATS
from pywps.app.Common import Metadata
from funcsigs import signature
import funcsigs

import logging
LOGGER = logging.getLogger("PYWPS")

def docstring_parser(doc):
    import re

    space = re.match('\n(\s+)', doc).groups()[0]

    i1 = re.search("Parameters\s+----------", doc).end()
    i2 = re.search("Return", doc).start()

    params = doc[i1:i2]
    return re.findall("{0}(\w+\s*:\s*.+(?:\n{0}\s+.*)+)".format(space), params)


def process_generator(func):
    """From an xclim indices, create a PyWPS process."""
    # Use the signature to define inputs.

    sig = signature(func)
    inputs = []
    for param in sig.parameters:
        if type(param.default) == int:
            pass



