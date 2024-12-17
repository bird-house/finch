"""Web Service Gateway Interface for PyWPS processes."""

import os
from pathlib import Path

import sentry_sdk
from pywps.app.Service import Service

from .processes import get_processes

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(os.environ["SENTRY_DSN"])


def create_app(cfgfiles=None):  # noqa: D103
    """Create PyWPS application."""
    config_files = [Path(__file__).parent.joinpath("default.cfg")]
    if isinstance(cfgfiles, str):
        cfgfiles = [cfgfiles]
    if cfgfiles:
        config_files += cfgfiles
    if "PYWPS_CFG" in os.environ:
        config_files.append(os.environ["PYWPS_CFG"])
    service = Service(cfgfiles=config_files)

    # delay the call of get_processes() so that the configuration is loaded
    # when instantiating the service
    service.processes = {p.identifier: p for p in get_processes()}

    return service


application = create_app()
