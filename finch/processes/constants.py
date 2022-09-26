from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from pywps import configuration
from xclim.testing import list_input_variables
import yaml


@dataclass
class DatasetConfiguration:
    """
    Attributes
    ----------
    path: str
        The path (or url) to the root directory where to search for the data.
    pattern: str
        The pattern of the filenames. Must include at least : "variable", "scenario" and "model".
        Patterns must be understandable by :py:func:`parse.parse`.
    local: bool
        Whether the path points to a local directory or a remote THREDDS catalog.
    depth : int
        The depth to which search for files below the directory. < 0 will search recursively.
    suffix : str
        When the files are local, this is the suffix of the files.
    allowed_values : dict
        Mapping from field name to a list of allowed values.
        Must include "scenario", "model" and "variable",
        the latter defines which variable are available and thus which indicator can be used.
    model_lists : dict
        A mapping from list name to a list of model names to provide special sublists.
        The values can also be a tuple of (model name, realization numer),
        in which case, pattern must include a "realization" field.
    """
    path: str
    pattern: str
    local: bool
    allowed_values: dict
    depth: int = 0
    suffix: str = '*nc'
    model_lists: dict = field(default_factory=dict)


def _read_dataset_config():
    p = Path(configuration.get_config_value('finch', 'dataset_config'))
    if not p.is_absolute():
        p = Path(__file__).parent.parent / p.name

    with p.open() as f:
        conf = yaml.safe_load(f)
    return {
        ds: DatasetConfiguration(**dsconf)
        for ds, dsconf in conf.items()
    }


datasets_config = _read_dataset_config()

available_variables = set(chain(*(d.allowed_values['variable'] for d in datasets_config.values())))
xclim_variables = set(list_input_variables(submodules=["atmos", "land", "seaIce"]).keys())

default_percentiles = {
    'days_over_precip_thresh': {'pr_per': 95},
    'days_over_precip_doy_thresh': {'pr_per': 95},
    'fraction_over_precip_doy_thresh': {'pr_per': 95},
    'fraction_over_precip_thresh': {'pr_per': 95},
    'cold_and_dry_days': {'pr_per': 25, 'tas_per': 25},
    'warm_and_dry_days': {'pr_per': 25, 'tas_per': 75},
    'warm_and_wet_days': {'pr_per': 75, 'tas_per': 75},
    'cold_and_wet_days': {'pr_per': 75, 'tas_per': 25},
    'tg90p': {'tas_per': 90},
    'tg10p': {'tas_per': 10},
    'tn90p': {'tasmin_per': 90},
    'tn10p': {'tasmin_per': 10},
    'tx90p': {'tasmax_per': 90},
    'tx10p': {'tasmax_per': 10},
    'cold_spell_duration_index': {'tasmin_per': 10},
    'warm_spell_duration_index': {'tasmax_per': 90},
}
