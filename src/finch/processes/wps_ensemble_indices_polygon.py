# noqa: D100
import logging

from anyascii import anyascii

from . import wpsio
from .ensemble_utils import ensemble_common_handler
from .subset import finch_subset_shape
from .utils import iter_xc_variables
from .wps_base import FinchProcess, convert_xclim_inputs_to_pywps

LOGGER = logging.getLogger("PYWPS")


class XclimEnsemblePolygonBase(FinchProcess):
    """Ensemble with polygon subset base class.

    Set xci to the xclim indicator in order to have a working class.
    """

    xci = None

    def __init__(self):
        """Create a WPS process from an xclim indicator class instance."""
        if self.xci is None:
            raise AttributeError(
                "Use the `finch.processes.wps_base.make_xclim_indicator_process` function instead."
            )

        xci_inputs, _ = convert_xclim_inputs_to_pywps(
            self.xci.parameters, self.xci.identifier, parse_percentiles=True
        )
        xci_inputs.extend(wpsio.xclim_common_options)
        self.xci_inputs_identifiers = [i.identifier for i in xci_inputs]

        inputs = [
            wpsio.shape,
            wpsio.start_date,
            wpsio.end_date,
            wpsio.ensemble_percentiles,
            wpsio.average,
            wpsio.temporal_average,
            *wpsio.get_ensemble_inputs(novar=True),
        ]

        # all other inputs that are not the xarray data (window, threshold, etc.)
        inputs.extend(
            [
                i
                for i in xci_inputs
                if i.identifier not in list(iter_xc_variables(self.xci))
            ]
        )

        inputs.extend(
            [wpsio.output_prefix, wpsio.output_format_netcdf_csv, wpsio.csv_precision]
        )

        outputs = [wpsio.output_netcdf_zip, wpsio.output_log]

        identifier = f"ensemble_polygon_{self.xci.identifier}"
        super().__init__(
            self._handler,
            identifier=identifier,
            version="0.1",
            title=anyascii(self.xci.title),
            abstract=anyascii(self.xci.abstract),
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
        return ensemble_common_handler(self, request, response, finch_subset_shape)
