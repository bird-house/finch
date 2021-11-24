from xclim.core.utils import VARIABLES

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

# a list of all posible netcdf arguments in xclim
# Read in the list of variables from xclim directly and add some other less documented.
xclim_netcdf_variables = set(VARIABLES.keys()).union(
    {
        "per",
        "q",
        "da",
        "tn10",
        "tn90",
        "tx90",
        "t10",
        "t90",
        "tas_25",
        "tas_75",
        "pr_25",
        "pr_75"
    }
)

bccaq_variables = {"tasmin", "tasmax", "pr"}
