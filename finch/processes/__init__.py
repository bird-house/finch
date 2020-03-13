import logging

from pywps.configuration import get_config_value
import xclim
import xclim.indicators.atmos
from xclim.core.indicator import Indicator

from .ensemble_utils import uses_accepted_netcdf_variables
from .wps_base import make_xclim_indicator_process
from .wps_bccaqv2_heatwave import BCCAQV2HeatWave
from .wps_ensemble_indices_bbox import XclimEnsembleBboxBase
from .wps_ensemble_indices_point import XclimEnsembleGridPointBase
from .wps_ensemble_indices_polygon import XclimEnsemblePolygonBase
from .wps_xclim_indices import XclimIndicatorBase
from .wps_xsubset_bbox import SubsetBboxProcess
from .wps_xsubset_bbox_dataset import SubsetBboxBCCAQV2Process, SubsetBboxDatasetProcess
from .wps_xsubset_point import SubsetGridPointProcess
from .wps_xsubset_point_dataset import (
    SubsetGridPointBCCAQV2Process,
    SubsetGridPointDatasetProcess,
)
from .wps_xsubset_polygon import SubsetPolygonProcess

logger = logging.getLogger("PYWPS")


def get_indicators(module):
    """For a given module, return the children that are instances of xclim.utils.Indicator."""
    return [o for o in module.__dict__.values() if isinstance(o, Indicator)]


# List of Indicators that are exposed as WPS processes
indicators = get_indicators(xclim.indicators.atmos)

for i in indicators:
    # Todo: remove me after xclim fixes the identifier name
    if i.compute.__name__ == 'hot_spell_max_length':
        i.identifier = 'hot_spell_max_length'

not_implemented = [
    "DC",  # lat input type is not implemented and start_up_mode argument seems to be missing?
    "growing_season_length",  # mid_date parameter not implemented
    "growing_season_end",  # mid_date parameter not implemented
    "last_spring_frost",  # before_date parameter not implemented
]
indicators = [i for i in indicators if i.identifier not in not_implemented]
ensemble_indicators = [i for i in indicators if uses_accepted_netcdf_variables(i)]


def get_processes(all_processes=False):
    """Get wps processes, using the current global `pywps` configuration"""
    default_dataset = get_config_value("finch", "default_dataset")
    datasets_configured = get_config_value("finch", f"dataset_{default_dataset}")

    if not datasets_configured:
        logger.warning("Datasets not configured. Some processes will not be available.")

    processes = []

    # xclim indicators
    for ind in indicators:
        suffix = "_Indicator_Process"
        base_class = XclimIndicatorBase
        processes.append(
            make_xclim_indicator_process(ind, suffix, base_class=base_class)
        )

    if datasets_configured or all_processes:
        # ensemble with grid point subset
        for ind in ensemble_indicators:
            suffix = "_Ensemble_GridPoint_Process"
            base_class = XclimEnsembleGridPointBase
            processes.append(
                make_xclim_indicator_process(ind, suffix, base_class=base_class)
            )

        # ensemble with bbox subset
        for ind in ensemble_indicators:
            suffix = "_Ensemble_Bbox_Process"
            base_class = XclimEnsembleBboxBase
            processes.append(
                make_xclim_indicator_process(ind, suffix, base_class=base_class)
            )
        # ensemble with polygon subset
        for ind in ensemble_indicators:
            suffix = "_Ensemble_Polygon_Process"
            base_class = XclimEnsemblePolygonBase
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
        SubsetPolygonProcess(),
    ]

    return processes


# Create virtual module for indicators so Sphinx can find it.
def _build_xclim():
    import sys

    processes = get_processes(all_processes=True)
    objs = {p.__class__.__name__: p.__class__ for p in processes}

    mod = xclim.indicators.build_module("finch.processes.xclim", objs, doc="""XCLIM Processes""")
    sys.modules["finch.processes.xclim"] = mod
    return mod


xclim = _build_xclim()
