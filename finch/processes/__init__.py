import logging

from pywps.configuration import get_config_value
import xclim
import xclim.atmos
from xclim.utils import Indicator

from .ensemble_utils import uses_accepted_netcdf_variables
from .wps_base import make_xclim_indicator_process
from .wps_bccaqv2_heatwave import BCCAQV2HeatWave
from .wps_ensemble_bbox_indices import XclimEnsembleBboxBase
from .wps_ensemble_gridpoint_indices import XclimEnsembleGridPointBase
from .wps_xclim_indices import XclimIndicatorBase
from .wps_xsubsetbbox import SubsetBboxProcess
from .wps_xsubsetbbox_dataset import SubsetBboxBCCAQV2Process, SubsetBboxDatasetProcess
from .wps_xsubsetpoint import SubsetGridPointProcess
from .wps_xsubsetpoint_dataset import (
    SubsetGridPointBCCAQV2Process,
    SubsetGridPointDatasetProcess,
)

logger = logging.getLogger("PYWPS")

datasets_configured = get_config_value(
    "finch", f"default_{get_config_value('finch', 'default_dataset')}"
)

if not datasets_configured:
    logger.warning("Datasets are not configured. Some processes will not be available.")


def get_indicators(module):
    """For a given module, return the children that are instances of xclim.utils.Indicator."""
    return [o for o in module.__dict__.values() if isinstance(o, Indicator)]


# List of Indicators that are exposed as WPS processes
indicators = get_indicators(xclim.atmos)

not_implemented = [
    "DC",  # lat input type is not implemented and start_up_mode argument seems to be missing?
]
indicators = [i for i in indicators if i.identifier not in not_implemented]
ensemble_indicators = [i for i in indicators if uses_accepted_netcdf_variables(i)]

processes = []

# xclim indicators
for ind in indicators:
    suffix = "Process"
    base_class = XclimIndicatorBase
    processes.append(make_xclim_indicator_process(ind, suffix, base_class=base_class))

if datasets_configured:
    # ensemble with grid point subset
    for ind in ensemble_indicators:
        suffix = "EnsembleGridPointProcess"
        base_class = XclimEnsembleGridPointBase
        processes.append(
            make_xclim_indicator_process(ind, suffix, base_class=base_class)
        )

    # ensemble with bbox subset
    for ind in ensemble_indicators:
        suffix = "EnsembleBboxProcess"
        base_class = XclimEnsembleBboxBase
        processes.append(
            make_xclim_indicator_process(ind, suffix, base_class=base_class)
        )

    processes += [
        SubsetGridPointDatasetProcess(),
        SubsetGridPointBCCAQV2Process(),
        SubsetBboxDatasetProcess(),
        SubsetBboxBCCAQV2Process(),
        BCCAQV2HeatWave(),
    ]

# others
processes += [
    SubsetBboxProcess(),
    SubsetGridPointProcess(),
]


# Create virtual module for indicators so Sphinx can find it.
def _build_xclim():
    import sys

    objs = {p.__class__.__name__: p.__class__ for p in processes}

    mod = xclim.build_module("finch.processes.xclim", objs, doc="""XCLIM Processes""")
    sys.modules["finch.processes.xclim"] = mod
    return mod


xclim = _build_xclim()
