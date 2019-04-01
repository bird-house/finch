import pytest

from pywps import Service
from pywps.tests import assert_response_success

from .common import get_output, CFG_FILE, client_for
from finch.processes import make_xclim_indicator_process
from xclim import temperature, streamflow
import xarray as xr
from pathlib import Path
from pywps import get_ElementMakerForVersion
import numpy as np

VERSION = "1.0.0"

WPS, OWS = get_ElementMakerForVersion(VERSION)


def test_wps_xclim_indices(tas_data_set):
    from pywps.tests import client_for

    client = client_for(Service(processes=[make_xclim_indicator_process('tg_mean', temperature.tg_mean)],
                                                                        cfgfiles=CFG_FILE))

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


def test_wps_freq_analysis(q_dataset):
    from pywps.tests import client_for

    client = client_for(Service(processes=[make_xclim_indicator_process('qfreq_analysis', streamflow.freq_analysis)],
                                                                        cfgfiles=CFG_FILE))
    fn = q_dataset(np.random.rand(4000))

    datainputs = "da=files@xlink:href=file://{fn};" \
                 "mode={mode};" \
                 "t={t};" \
                 "dist={dist}".format(fn=fn, mode="max", t=10, dist="norm")

    #resp = client.get(service='WPS', request='Execute', version='1.0.0', identifier='qfreq_analysis',
    #                  datainputs=datainputs)
    resp = client.get("?service=WPS&request=Execute&version=1.0.0&identifier=qfreq_analysis&datainputs={}".format(
        datainputs))
    print(resp.response[0])
    assert_response_success(resp)


def test_wps_xclim_heat_wave_frequency(tasmin_data_set, tasmax_data_set):
    process = make_xclim_indicator_process('heat_wave_frequency', temperature.heat_wave_frequency)
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


