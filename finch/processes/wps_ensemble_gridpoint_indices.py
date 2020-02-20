import logging

from unidecode import unidecode

from finch.processes.subset import finch_subset_gridpoint

from . import wpsio
from .wps_base import FinchProcess, convert_xclim_inputs_to_pywps
from .ensemble_utils import ensemble_common_handler, xclim_netcdf_variables

LOGGER = logging.getLogger("PYWPS")


class XclimEnsembleGridPointBase(FinchProcess):
    """Ensemble with grid point subset base class

    Set xci to the xclim indicator in order to have a working class"""

    xci = None

    def __init__(self):
        """Create a WPS process from an xclim indicator class instance."""

        if self.xci is None:
            raise AttributeError(
                "Use the `finch.processes.wps_base.make_xclim_indicator_process` function instead."
            )

        attrs = self.xci.json()
        xci_inputs = convert_xclim_inputs_to_pywps(eval(attrs["parameters"]))
        self.xci_inputs_identifiers = [i.identifier for i in xci_inputs]

        inputs = [
            wpsio.lat,
            wpsio.lon,
            wpsio.start_date,
            wpsio.end_date,
            wpsio.ensemble_percentiles,
            wpsio.dataset_name,
        ]
        rcp = wpsio.copy_io(wpsio.rcp, min_occurs=1)
        inputs.append(rcp)

        # all other inputs that are not the xarray data (window, threshold, etc.)
        for i in xci_inputs:
            if i.identifier not in xclim_netcdf_variables:
                inputs.append(i)

        inputs.append(wpsio.output_format_netcdf_csv)

        outputs = [wpsio.output_netcdf_zip, wpsio.output_log]

        identifier = f"ensemble_grid_point_{attrs['identifier']}"
        super().__init__(
            self._handler,
            identifier=identifier,
            version="0.1",
            title=unidecode(attrs["long_name"]),
            abstract=unidecode(attrs["abstract"]),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {
            "start": 5,
            "subset": 7,
            "compute_indices": 50,
            "convert_to_csv": 95,
            "done": 99,
        }

    def _handler(self, request, response):
        return ensemble_common_handler(self, request, response, finch_subset_gridpoint)
