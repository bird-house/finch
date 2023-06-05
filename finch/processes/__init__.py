# noqa: D104
import logging
from pathlib import Path

from pywps.configuration import get_config_value
from xclim.core.indicator import registry as xclim_registry

from .ensemble_utils import uses_accepted_netcdf_variables
from .utils import get_available_variables, get_datasets_config, get_virtual_modules
from .wps_base import make_xclim_indicator_process
from .wps_ensemble_indices_bbox import XclimEnsembleBboxBase
from .wps_ensemble_indices_point import XclimEnsembleGridPointBase
from .wps_ensemble_indices_polygon import XclimEnsemblePolygonBase
from .wps_geoseries_to_netcdf import GeoseriesToNetcdfProcess
from .wps_hourly_to_daily import HourlyToDailyProcess
from .wps_sdba import EmpiricalQuantileMappingProcess
from .wps_xaverage_polygon import AveragePolygonProcess
from .wps_xclim_indices import XclimIndicatorBase
from .wps_xsubset_bbox import SubsetBboxProcess
from .wps_xsubset_bbox_dataset import SubsetBboxDatasetProcess
from .wps_xsubset_point import SubsetGridPointProcess
from .wps_xsubset_point_dataset import SubsetGridPointDatasetProcess
from .wps_xsubset_polygon import SubsetPolygonProcess

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
            and (
                ind.identifier.upper() == ind._registry_id  # official indicator
                or ind._registry_id.startswith(
                    "xclim.core.indicator"
                )  # oups. Bug for discharge_distribution_fit in xclim 0.40
            )
        )

    out = dict(filter(filter_func, xclim_registry.items()))
    return [ind.get_instance() for ind in out.values()]


not_implemented = [
    "DC",
    "FWI",
    "RH",
    "RH_FROMDEWPOINT",
    "E_SAT",
    "HUSS",
]


def get_processes():
    """Get wps processes using the current global `pywps` configuration."""
    indicators = get_indicators(
        realms=["atmos", "land", "seaIce"], exclude=not_implemented
    )
    mod_dict = get_virtual_modules()
    for mod in mod_dict.keys():
        indicators.extend(mod_dict[mod]["indicators"])

    ds_conf = get_datasets_config()
    if ds_conf:
        available_variables = get_available_variables()
        ensemble_indicators = [
            i
            for i in indicators
            if uses_accepted_netcdf_variables(i, available_variables)
        ]
    else:
        ensemble_indicators = []
        logger.warning(
            "No ensemble datasets configured, many processes won't be available."
        )
        default_dataset = get_config_value("finch", "default_dataset")
        if default_dataset not in ds_conf:
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
    processes += [EmpiricalQuantileMappingProcess()]

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

    if ensemble_indicators:
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
        GeoseriesToNetcdfProcess(),
    ]

    return processes
