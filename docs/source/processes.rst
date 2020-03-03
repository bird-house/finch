.. _processes:

Processes
=========

.. contents::
    :local:
    :depth: 1

..
    from finch.processes import get_processes
    processes = get_processes(all_processes=True)
    name = lambda p: p.__class__.__name__
    ensemble = sorted([p for p in processes if "Ensemble" in name(p)], key=name)
    indicators = sorted([p for p in processes if name(p).endswith('_Indicator_Process')], key=name)
    others = sorted([p for p in processes if name(p) not in set(map(name, indicators + ensemble))], key=name)
    format = lambda p: print(f'.. autoprocess:: finch.processes.xclim.{name(p)}\n')
    def print_all():
        print("xclim Indicators")
        print("----------------")
        list(map(format, indicators))
        print("Ensemble Processes")
        print("------------------")
        list(map(format, ensemble))
        print("Other Processes")
        print("---------------")
        list(map(format, others))

    print_all()


xclim Indicators 
----------------
.. autoprocess:: finch.processes.xclim.cdd_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cwd_Indicator_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Indicator_Process

.. autoprocess:: finch.processes.xclim.dtr_Indicator_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Indicator_Process

.. autoprocess:: finch.processes.xclim.etr_Indicator_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Indicator_Process

.. autoprocess:: finch.processes.xclim.frost_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.ice_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Indicator_Process

.. autoprocess:: finch.processes.xclim.prcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Indicator_Process

.. autoprocess:: finch.processes.xclim.rx1day_Indicator_Process

.. autoprocess:: finch.processes.xclim.sdii_Indicator_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg10p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg90p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn10p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn90p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_min_Indicator_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx10p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx90p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_min_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.wetdays_Indicator_Process

Ensemble Processes
------------------
.. autoprocess:: finch.processes.xclim.cdd_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cdd_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cwd_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cwd_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dtr_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dtr_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.etr_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.etr_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.frost_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.frost_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.ice_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.ice_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.prcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.prcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.rx1day_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.rx1day_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.sdii_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.sdii_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg10p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg10p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg90p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg90p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn10p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn10p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn90p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn90p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_max_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_max_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_min_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_min_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx10p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx10p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx90p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx90p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_max_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_max_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_min_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_min_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.wetdays_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.wetdays_Ensemble_GridPoint_Process

Other Processes
---------------
.. autoprocess:: finch.processes.xclim.BCCAQV2HeatWave

.. autoprocess:: finch.processes.xclim.SubsetBboxBCCAQV2Process

.. autoprocess:: finch.processes.xclim.SubsetBboxDatasetProcess

.. autoprocess:: finch.processes.xclim.SubsetBboxProcess

.. autoprocess:: finch.processes.xclim.SubsetGridPointBCCAQV2Process

.. autoprocess:: finch.processes.xclim.SubsetGridPointDatasetProcess

.. autoprocess:: finch.processes.xclim.SubsetGridPointProcess
