import zipfile

from dask.diagnostics import ProgressBar
from dask.diagnostics.progress import format_time
from pathlib import Path
from pywps import Process, ComplexInput, LiteralInput
from sentry_sdk import configure_scope
import logging

from finch.processes.utils import is_opendap_url

LOGGER = logging.getLogger("PYWPS")


class FinchProcess(Process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Must be assigned to the instance so that
        # it's also copied over when the process is deepcopied
        self.wrapped_handler = self.handler
        self.handler = self._handler_wrapper
        self.response = None
        self.percentage = None

    def _handler_wrapper(self, request, response):
        self.sentry_configure_scope(request)

        # The process has been deepcopied, so it's ok to assign it a single response.
        # We can now update the status document from the process instance itself.
        self.reponse = response
        return self.wrapped_handler(request, response)

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
                scope.set_extra("host", request.http_request.host)
                scope.set_extra("remote_addr", request.http_request.remote_addr)
                scope.set_extra("xml_request", request.http_request.data)


class FinchProgressBar(ProgressBar):
    def __init__(self, logging_function, start_percentage, *args, **kwargs):
        super(FinchProgressBar, self).__init__(*args, **kwargs)
        self._logging_function = logging_function
        self._start_percentage = start_percentage

    def _draw_bar(self, frac, elapsed):
        start = self._start_percentage / 100

        frac += start - frac * start
        bar = "#" * int(self._width * frac)
        percent = int(100 * frac)
        elapsed = format_time(elapsed)
        msg = "[{0:<{1}}] | {2}% Done | {3}".format(bar, self._width, percent, elapsed)

        self._logging_function(msg, percent)
