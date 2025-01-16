# noqa: D205,D400
"""
Processes as a virtual submodule
================================
When imported, this module exposes the default list of processes as virtual modules : indicators, ensemble and other.
It forces the loading of the "default.cfg" file if no datasets were configured.

It is meant to provide sphinx with something to document, not to be used in reality.
We needed to have this code within finch, so that the autodoc mock imports are functional.
"""
from pathlib import Path
from types import ModuleType

from pywps.configuration import get_config_value, load_configuration

from finch.processes import get_processes

if not get_config_value("finch", "datasets_config"):
    load_configuration(Path(__file__).parent.parent / "default.cfg")

processes = sorted(get_processes(), key=lambda p: p.__class__.__name__)

ens_proc = {
    p.__class__.__name__: p.__class__
    for p in processes
    if "Ensemble" in p.__class__.__name__
}
ind_proc = {
    p.__class__.__name__: p.__class__
    for p in processes
    if p.__class__.__name__.endswith("_Indicator_Process")
}
oth_proc = {
    p.__class__.__name__: p.__class__
    for p in processes
    if p.__class__.__name__ not in (list(ens_proc) + list(ind_proc))
}

indicators = ModuleType("indicators", "Indicators Processes\n====================")
indicators.__dict__.update(ind_proc)

ensemble = ModuleType("ensemble", "Ensemble Processes\n==================")
ensemble.__dict__.update(ens_proc)

other = ModuleType("other", "Other Processes\n===============")
other.__dict__.update(oth_proc)
