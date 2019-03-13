import pytest

from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, CFG_FILE
from finch.processes import XclimIndicatorProcess
from xclim import temperature
import xarray as xr
from pathlib import Path
from pywps import get_ElementMakerForVersion


VERSION = "1.0.0"

WPS, OWS = get_ElementMakerForVersion(VERSION)


def test_wps_xclim_indices(tas_data_set):
    client = client_for(Service(processes=[XclimIndicatorProcess(temperature.tg_mean)], cfgfiles=CFG_FILE))

    datainputs = "tas=files@xlink:href=file://{fn};" \
                 "freq={freq}".format(fn=tas_data_set,
                                      freq='MS')

    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=tg_mean&datainputs={}".format(
            datainputs))

    assert_response_success(resp)
    out = get_output(resp.xml)
    p = Path(out['output_netcdf'])
    fn = Path('/').joinpath(*p.parts[1:])
    ds = xr.open_dataset(fn)
    assert ds.tg_mean.standard_name == 'air_temperature'


def test_wps_xclim_heat_wave_frequency(tasmin_data_set, tasmax_data_set):
    process = XclimIndicatorProcess(temperature.heat_wave_frequency)
    client = client_for(Service(processes=[process], cfgfiles=CFG_FILE))

    request_doc = WPS.Execute(
        OWS.Identifier('heat_wave_frequency'),
        WPS.DataInputs(
            WPS.Input(
                OWS.Identifier('tasmax'),
                WPS.Reference(
                    WPS.Body('request body'),
                    {'{http://www.w3.org/1999/xlink}href': 'file://' + tasmax_data_set},
                    method='POST'
                )
            ),
            WPS.Input(
                OWS.Identifier('tasmin'),
                WPS.Reference(
                    WPS.Body('request body'),
                    {'{http://www.w3.org/1999/xlink}href': 'file://' + tasmin_data_set},
                    method='POST'
                )
            )
        ),
        version='1.0.0'
    )
    resp = client.post_xml(doc=request_doc)

    assert_response_success(resp)
    out = get_output(resp.xml)
    p = Path(out['output_netcdf'])
    fn = Path('/').joinpath(*p.parts[1:])
    ds = xr.open_dataset(fn)

    assert ds.heat_wave_frequency.standard_name == 'heat_wave_events'
