.. _processes:

Processes
=========

.. contents::
    :local:
    :depth: 1

..
   from finch.processes import processes
   processes.sort(key=lambda x: x.__class__.__name__)
   for p in processes:
       c = p.__class__
       doc = '.. autoprocess:: {}.{}\n'
       print(doc.format(c.__module__, c.__name__))


xclim Indicators
----------------

.. autoprocess:: finch.processes.xclim.base_flow_indexProcess

.. autoprocess:: finch.processes.xclim.cold_spell_daysProcess

.. autoprocess:: finch.processes.xclim.cold_spell_duration_indexProcess

.. autoprocess:: finch.processes.xclim.consecutive_frost_daysProcess

.. autoprocess:: finch.processes.xclim.cooling_degree_daysProcess

.. autoprocess:: finch.processes.xclim.daily_freezethaw_cyclesProcess

.. autoprocess:: finch.processes.xclim.daily_pr_intensityProcess

.. autoprocess:: finch.processes.xclim.daily_temperature_rangeProcess

.. autoprocess:: finch.processes.xclim.daily_temperature_range_variabilityProcess

.. autoprocess:: finch.processes.xclim.doy_qmaxProcess

.. autoprocess:: finch.processes.xclim.doy_qminProcess

.. autoprocess:: finch.processes.xclim.extreme_temperature_rangeProcess

.. autoprocess:: finch.processes.xclim.freq_analysisProcess

.. autoprocess:: finch.processes.xclim.freshet_startProcess

.. autoprocess:: finch.processes.xclim.frost_daysProcess

.. autoprocess:: finch.processes.xclim.growing_degree_daysProcess

.. autoprocess:: finch.processes.xclim.growing_season_lengthProcess

.. autoprocess:: finch.processes.xclim.heat_wave_frequencyProcess

.. autoprocess:: finch.processes.xclim.heat_wave_indexProcess

.. autoprocess:: finch.processes.xclim.heat_wave_max_lengthProcess

.. autoprocess:: finch.processes.xclim.heating_degree_daysProcess

.. autoprocess:: finch.processes.xclim.ice_daysProcess

.. autoprocess:: finch.processes.xclim.max_1day_precipitation_amountProcess

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amountProcess

.. autoprocess:: finch.processes.xclim.maximum_consecutive_dry_daysProcess

.. autoprocess:: finch.processes.xclim.maximum_consecutive_wet_daysProcess

.. autoprocess:: finch.processes.xclim.precip_accumulationProcess

.. autoprocess:: finch.processes.xclim.rain_on_frozen_ground_daysProcess

.. autoprocess:: finch.processes.xclim.statsProcess

.. autoprocess:: finch.processes.xclim.tg10pProcess

.. autoprocess:: finch.processes.xclim.tg90pProcess

.. autoprocess:: finch.processes.xclim.tg_meanProcess

.. autoprocess:: finch.processes.xclim.tn10pProcess

.. autoprocess:: finch.processes.xclim.tn90pProcess

.. autoprocess:: finch.processes.xclim.tn_days_belowProcess

.. autoprocess:: finch.processes.xclim.tn_maxProcess

.. autoprocess:: finch.processes.xclim.tn_meanProcess

.. autoprocess:: finch.processes.xclim.tn_minProcess

.. autoprocess:: finch.processes.xclim.tropical_nightsProcess

.. autoprocess:: finch.processes.xclim.tx10pProcess

.. autoprocess:: finch.processes.xclim.tx90pProcess

.. autoprocess:: finch.processes.xclim.tx_days_aboveProcess

.. autoprocess:: finch.processes.xclim.tx_maxProcess

.. autoprocess:: finch.processes.xclim.tx_meanProcess

.. autoprocess:: finch.processes.xclim.tx_minProcess

.. autoprocess:: finch.processes.xclim.tx_tn_days_aboveProcess

.. autoprocess:: finch.processes.xclim.wetdaysProcess
