import xclim.indicators.atmos

from finch.processes.wps_base import make_xclim_indicator_process
from finch.processes.wps_xclim_indices import XclimIndicatorBase


def test_locales_simple():
    base_class = XclimIndicatorBase
    indicator = make_xclim_indicator_process(
        xclim.indicators.atmos.cold_spell_days, "_suffix", base_class
    )
    assert "fr" in indicator.translations
    assert "title" in indicator.translations["fr"]
