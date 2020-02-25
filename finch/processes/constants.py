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
    ("HadGEM2-CC", "r1"),
    ("CanESM2", "r1"),
    ("MRI-CGCM3", "r1"),
    ("inmcm4", "r1"),
    ("CSIRO-Mk3-6-0", "r1"),
    ("MPI-ESM-LR", "r3"),
    ("HadGEM2-ES", "r1"),
    ("GFDL-ESM2G", "r1"),
    ("CCSM4", "r2"),
    ("ACCESS1-0", "r1"),
    ("CNRM-CM5", "r1"),
    ("MIROC5", "r3"),
]

ALL_24_MODELS = "all_24_models"
PCIC_12 = "pcic_12"

ALLOWED_MODEL_NAMES = BCCAQV2_MODELS + [ALL_24_MODELS, PCIC_12]

# a list of all posible netcdf arguments in xclim
xclim_netcdf_variables = {
    "tasmin",
    "tasmax",
    "tas",
    "pr",
    "prsn",
    "tn10",
    "tn90",
    "t10",
    "t90",
}

bccaq_variables = {"tasmin", "tasmax", "pr"}
