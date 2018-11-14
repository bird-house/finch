from .wps_xclim_indices import UnivariateXclimIndicatorProcess
import xclim.temperature
import xclim.precip


def get_indicators(*args):
    """For all modules or classes listed, return the children that are instances of xclim.utils.Indicator."""
    from xclim.utils import Indicator
    #  from xclim.temperature import Tas

    out = []
    for obj in args:
        for key, val in obj.__dict__.items():
            if isinstance(val, Indicator):
                out.append(val)

    return out


# List of Indicators that are exposed as WPS processes
indicators = get_indicators(xclim.temperature, xclim.precip)

# Instantiate processes
processes = [UnivariateXclimIndicatorProcess(i) for i in indicators]

