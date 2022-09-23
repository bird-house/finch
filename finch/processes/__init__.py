import logging

from pywps.configuration import get_config_value
import xclim

from .constants import datasets_config
from .ensemble_utils import uses_accepted_netcdf_variables
from .wps_base import make_xclim_indicator_process
from .wps_ensemble_indices_bbox import XclimEnsembleBboxBase
from .wps_ensemble_indices_point import XclimEnsembleGridPointBase
from .wps_ensemble_indices_polygon import XclimEnsemblePolygonBase
from .wps_xclim_indices import XclimIndicatorBase
from .wps_xsubset_bbox import SubsetBboxProcess
from .wps_xsubset_bbox_dataset import SubsetBboxDatasetProcess
from .wps_xsubset_point import SubsetGridPointProcess
from .wps_xsubset_point_dataset import SubsetGridPointDatasetProcess
from .wps_xsubset_polygon import SubsetPolygonProcess
from .wps_sdba import EmpiricalQuantileMappingProcess
from .wps_xaverage_polygon import AveragePolygonProcess
from .wps_hourly_to_daily import HourlyToDailyProcess
from .wps_geoseries_to_netcdf import GeoseriesToNetcdfProcess

logger = logging.getLogger("PYWPS")
logger.disabled = False


def get_indicators(realms=["atmos"], exclude=()):
    """For all modules or classes listed, return the children that are instances of registered Indicator classes.

    module : A xclim module.
    """

    def filter_func(elem):
        name, ind = elem
        return (
            ind.realm in realms
            and ind.identifier is not None
            and name not in exclude
            and ind.identifier.upper() == ind._registry_id  # official indicator
        )

    out = dict(filter(filter_func, xclim.core.indicator.registry.items()))
    return [ind.get_instance() for ind in out.values()]


not_implemented = [
    "DC",
    "FWI",
    "RH",
    "RH_FROMDEWPOINT",
    "E_SAT",
    "HUSS",
]


indicators = get_indicators(realms=["atmos", "land", "seaIce"], exclude=not_implemented)
ensemble_indicators = [i for i in indicators if uses_accepted_netcdf_variables(i)]


def get_processes(all_processes=False):
    """Get wps processes, using the current global `pywps` configuration"""
    default_dataset = get_config_value("finch", "default_dataset")

    if not datasets_config:
        logger.warning("The datasets configured, many processes won't be available.")
    if default_dataset not in datasets_config:
        logger.warning("The default dataset is not configured, which is weird.")

    processes = []

    # xclim indicators
    for ind in indicators:
        suffix = "_Indicator_Process"
        base_class = XclimIndicatorBase
        processes.append(
            make_xclim_indicator_process(ind, suffix, base_class=base_class)
        )

    # Statistical downscaling and bias adjustment
    processes += [
        EmpiricalQuantileMappingProcess()
    ]

    if datasets_config or all_processes:
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
            SubsetBboxDatasetProcess(),
        ]

    # others
    processes += [
        SubsetBboxProcess(),
        SubsetGridPointProcess(),
        SubsetPolygonProcess(),
        AveragePolygonProcess(),
        HourlyToDailyProcess(),
        GeoseriesToNetcdfProcess()
    ]

    return processes


# Create virtual module for indicators so Sphinx can find it.
def _build_xclim():
    import sys

    processes = get_processes(all_processes=True)
    objs = {p.__class__.__name__: p.__class__ for p in processes}

    mod = xclim.core.indicator.build_indicator_module(
        "finch.processes.xclim", objs, doc="""XCLIM Processes"""
    )
    sys.modules["finch.processes.xclim"] = mod
    return mod


xclim = _build_xclim()  # noqa
