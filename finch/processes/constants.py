from xclim.testing import list_input_variables

BCCAQV2_MODELS = [
    "BNU-ESM",
    "CCSM4",
    "CESM1-CAM5",
    "CNRM-CM5",
    "CSIRO-Mk3-6-0",
    "CanESM2",
    "FGOALS-g2",
    "GFDL-CM3",
    "GFDL-ESM2G",
    "GFDL-ESM2M",
    "HadGEM2-AO",
    "HadGEM2-ES",
    "IPSL-CM5A-LR",
    "IPSL-CM5A-MR",
    "MIROC-ESM-CHEM",
    "MIROC-ESM",
    "MIROC5",
    "MPI-ESM-LR",
    "MPI-ESM-MR",
    "MRI-CGCM3",
    "NorESM1-M",
    "NorESM1-ME",
    "bcc-csm1-1-m",
    "bcc-csm1-1",
]

# taken from: https://www.pacificclimate.org/data/statistically-downscaled-climate-scenarios
PCIC_12_MODELS_REALIZATIONS = [
    ("ACCESS1-0", "r1"),
    ("CCSM4", "r2"),
    ("CNRM-CM5", "r1"),
    ("CSIRO-Mk3-6-0", "r1"),
    ("CanESM2", "r1"),
    ("GFDL-ESM2G", "r1"),
    ("HadGEM2-CC", "r1"),
    ("HadGEM2-ES", "r1"),
    ("MIROC5", "r3"),
    ("MPI-ESM-LR", "r3"),
    ("MRI-CGCM3", "r1"),
    ("inmcm4", "r1"),
]


ALL_24_MODELS = "24MODELS"
PCIC_12 = "PCIC12"

ALLOWED_MODEL_NAMES = [ALL_24_MODELS, PCIC_12] + BCCAQV2_MODELS

bccaq_variables = {"tasmin", "tasmax", "pr"}

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
