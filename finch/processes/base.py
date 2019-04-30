from dask.diagnostics import ProgressBar
from dask.diagnostics.progress import format_time
from pywps import Process
from sentry_sdk import configure_scope
import xarray as xr
import requests
import logging
import os

LOGGER = logging.getLogger("PYWPS")


class FinchProcess(Process):

    def try_opendap(self, input):
        """Try to open the file as an OPeNDAP url and chunk it. If OPeNDAP fails, access the file directly. In both
        cases, return an xarray.Dataset.
        """
        url = input.url
        if url and not url.startswith("file"):
            r = requests.get(url + ".dds")
            if r.status_code == 200 and r.content.decode().startswith("Dataset"):
                ds = xr.open_dataset(url)
                chunks = chunk_dataset(ds, max_size=1000000)
                ds = ds.chunk(chunks)
                self.write_log("Opened dataset as an OPeNDAP url: {}".format(url))
                return ds

        self.write_log("Downloading dataset for url: {}".format(url))

        # Accessing the file property loads the data in the data property
        # and writes it to disk
        ds = xr.open_dataset(input.file)

        # We need to cleanup the data property, otherwise it will be
        # written in the database and to the output status xml file
        # and it can get too large.
        input._data = ""
        return ds

    def log_file_path(self):
        return os.path.join(self.workdir, 'log.txt')

    def write_log(self, message):
        open(self.log_file_path(), "a").write(message + "\n")
        LOGGER.info(message)

    def sentry_configure_scope(self, request):
        """Add additional data to sentry error messages.

        When sentry is not initialized, this won't add any overhead.
        """
        with configure_scope() as scope:
            scope.set_extra("identifier", self.identifier)
            scope.set_extra("request_uuid", str(self.uuid))
            if request.http_request:
                # if the request has been put in the `stored_requests` table by pywps
                # the original request.http_request is not available anymore
                scope.set_extra("remote_addr", request.http_request.remote_addr)
                scope.set_extra("xml_request", request.http_request.data)


def chunk_dataset(ds, max_size=1000000):
    """Ensures the chunked size of a xarray.Dataset is below a certain size

    Cycle through the dimensions, divide the chunk size by 2 until criteria is met.
    """
    from functools import reduce
    from operator import mul
    from itertools import cycle

    chunks = dict(ds.sizes)

    def chunk_size():
        return reduce(mul, chunks.values())

    for dim in cycle(chunks):
        if chunk_size() < max_size:
            break
        chunks[dim] = max(chunks[dim] // 2, 1)

    return chunks


class FinchProgress(ProgressBar):
    def __init__(self, logging_function, start_percentage, *args, **kwargs):
        super(FinchProgress, self).__init__(*args, **kwargs)
        self._logging_function = logging_function
        self._start_percentage = start_percentage

    def _draw_bar(self, frac, elapsed):
        start = self._start_percentage / 100

        frac += start - frac * start
        bar = '#' * int(self._width * frac)
        percent = int(100 * frac)
        elapsed = format_time(elapsed)
        msg = '[{0:<{1}}] | {2}% Done | {3}'.format(bar, self._width, percent, elapsed)

        self._logging_function(msg, percent)
