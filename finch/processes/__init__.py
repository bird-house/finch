from .wps_xsubsetbbox import SubsetBboxProcess
from .wps_xsubsetpoint import SubsetGridPointProcess
from .wps_subset_polygon import SubsetPolygonProcess
from .wps_xsubset_bccaqv2 import SubsetBCCAQV2Process
from .wps_xsubsetpoint_bccaqv2 import SubsetGridPointBCCAQV2Process
from .wps_xsubsetbbox_bccaqv2 import SubsetBboxBCCAQV2Process
from .wps_xclim_indices import make_xclim_indicator_process
from .wps_bccaqv2_heatwave import BCCAQV2HeatWave
import xclim
import xclim.atmos


def get_indicators(*args):
    """For all modules or classes listed, return the children that are instances of xclim.utils.Indicator."""
    from xclim.utils import Indicator

    out = []
    for obj in args:
        for key, val in obj.__dict__.items():
            if isinstance(val, Indicator):
                out.append(val)

    return out


# List of Indicators that are exposed as WPS processes
indicators = get_indicators(xclim.atmos)

# Create PyWPS.Process subclasses
processes = [make_xclim_indicator_process(ind) for ind in indicators]
processes.extend(
    [
        SubsetBboxProcess(),
        SubsetGridPointProcess(),
        SubsetPolygonProcess(),
        SubsetBCCAQV2Process(),
        SubsetGridPointBCCAQV2Process(),
        SubsetBboxBCCAQV2Process(),
        BCCAQV2HeatWave(),
    ]
)


# Create virtual module for indicators so Sphinx can find it.
def _build_xclim():
    import sys

    objs = {p.__class__.__name__: p.__class__ for p in processes}

    mod = xclim.build_module("finch.processes.xclim", objs, doc="""XCLIM Processes""")
    sys.modules["finch.processes.xclim"] = mod
    return mod


xclim = _build_xclim()
