import xclim
import xclim.atmos
from xclim.utils import Indicator

from finch.processes.ensemble_utils import uses_bccaqv2_data
from finch.processes.wps_xclim_indices import XclimIndicatorBase

from .wps_base import make_xclim_indicator_process
from .wps_ensemble_gridpoint_indices import XclimEnsembleGridPointBase
from .wps_ensemble_bbox_indices import XclimEnsembleBboxBase
from .wps_bccaqv2_heatwave import BCCAQV2HeatWave
from .wps_xsubsetbbox import SubsetBboxProcess
from .wps_xsubsetbbox_bccaqv2 import SubsetBboxBCCAQV2Process
from .wps_xsubsetpoint import SubsetGridPointProcess
from .wps_xsubsetpoint_bccaqv2 import SubsetGridPointBCCAQV2Process


def get_indicators(module):
    """For a given module, return the children that are instances of xclim.utils.Indicator."""
    return [o for o in module.__dict__.values() if isinstance(o, Indicator)]


# List of Indicators that are exposed as WPS processes
indicators = get_indicators(xclim.atmos)

not_implemented = [
    "DC",  # lat input type is not implemented and start_up_mode argument seems to be missing?
]
indicators = [i for i in indicators if i.identifier not in not_implemented]
ensemble_indicators = [i for i in indicators if uses_bccaqv2_data(i)]

processes = []

# xclim indicators
for ind in indicators:
    suffix = "_Indicator_Process"
    base_class = XclimIndicatorBase
    processes.append(make_xclim_indicator_process(ind, suffix, base_class=base_class))

# ensemble with grid point subset
for ind in ensemble_indicators:
    suffix = "_Ensemble_GridPoint_Process"
    base_class = XclimEnsembleGridPointBase
    processes.append(make_xclim_indicator_process(ind, suffix, base_class=base_class))

# ensemble with bbox subset
for ind in ensemble_indicators:
    suffix = "_Ensemble_Bbox_Process"
    base_class = XclimEnsembleBboxBase
    processes.append(make_xclim_indicator_process(ind, suffix, base_class=base_class))

# others
processes += [
    SubsetBboxProcess(),
    SubsetGridPointProcess(),
    SubsetGridPointBCCAQV2Process(),
    SubsetBboxBCCAQV2Process(),
    BCCAQV2HeatWave(),
]


# Create virtual module for indicators so Sphinx can find it.
def _build_xclim():
    import sys

    objs = {p.__class__.__name__: p.__class__ for p in processes}

    mod = xclim.build_module("finch.processes.xclim", objs, doc="""XCLIM Processes""")
    sys.modules["finch.processes.xclim"] = mod
    return mod


xclim = _build_xclim()
