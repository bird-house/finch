from .wps_xclim_indices import make_xclim_indicator_process
from xclim import build_module
import xclim.temperature
import xclim.precip


def get_indicators(*args):
    """For all modules or classes listed, return the children that are instances of xclim.utils.Indicator."""
    from xclim.utils import Indicator
    #  from xclim.temperature import Tas

    out = []
    for obj in args:
        for key, val in obj.__dict__.items():
            if isinstance(val, Indicator):
                out.append(val)

    return out


# List of Indicators that are exposed as WPS processes
indicators = get_indicators(xclim.temperature, xclim.precip)

# Create PyWPS.Process subclasses
processes = [make_xclim_indicator_process(ind) for ind in indicators]


# Create virtual module for indicators so Sphinx can find it.
def _build_xclim():
    import sys

    objs = {p.__class__.__name__: p.__class__ for p in processes}

    mod = build_module('finch.processes.xclim', objs, doc="""XCLIM Processes""")
    sys.modules['finch.processes.xclim'] = mod
    return mod


xclim = _build_xclim()
