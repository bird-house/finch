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
.. autoprocess:: finch.processes.xclim.base_flow_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.biologically_effective_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.blowing_snow_Indicator_Process

.. autoprocess:: finch.processes.xclim.calm_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cdd_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_and_dry_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_and_wet_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.cold_spell_frequency_Indicator_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_free_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.continuous_snow_cover_end_Indicator_Process

.. autoprocess:: finch.processes.xclim.continuous_snow_cover_start_Indicator_Process

.. autoprocess:: finch.processes.xclim.cool_night_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.corn_heat_units_Indicator_Process

.. autoprocess:: finch.processes.xclim.cwd_Indicator_Process

.. autoprocess:: finch.processes.xclim.days_over_precip_thresh_Indicator_Process

.. autoprocess:: finch.processes.xclim.days_with_snow_Indicator_Process

.. autoprocess:: finch.processes.xclim.degree_days_exceedance_date_Indicator_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Indicator_Process

.. autoprocess:: finch.processes.xclim.doy_qmax_Indicator_Process

.. autoprocess:: finch.processes.xclim.doy_qmin_Indicator_Process

.. autoprocess:: finch.processes.xclim.dry_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.dry_spell_frequency_Indicator_Process

.. autoprocess:: finch.processes.xclim.dry_spell_total_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.dtr_Indicator_Process

.. autoprocess:: finch.processes.xclim.dtrmax_Indicator_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Indicator_Process

.. autoprocess:: finch.processes.xclim.effective_growing_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.etr_Indicator_Process

.. autoprocess:: finch.processes.xclim.fire_season_Indicator_Process

.. autoprocess:: finch.processes.xclim.first_day_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.first_day_below_Indicator_Process

.. autoprocess:: finch.processes.xclim.first_snowfall_Indicator_Process

.. autoprocess:: finch.processes.xclim.fit_Indicator_Process

.. autoprocess:: finch.processes.xclim.fraction_over_precip_thresh_Indicator_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_frequency_Indicator_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_max_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_mean_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.freezing_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.freq_analysis_Indicator_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Indicator_Process

.. autoprocess:: finch.processes.xclim.frost_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_end_Indicator_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_start_Indicator_Process

.. autoprocess:: finch.processes.xclim.frost_season_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.growing_season_end_Indicator_Process

.. autoprocess:: finch.processes.xclim.growing_season_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.growing_season_start_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.high_precip_low_temp_Indicator_Process

.. autoprocess:: finch.processes.xclim.hot_spell_frequency_Indicator_Process

.. autoprocess:: finch.processes.xclim.hot_spell_max_length_Indicator_Process

.. autoprocess:: finch.processes.xclim.huglin_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.humidex_Indicator_Process

.. autoprocess:: finch.processes.xclim.hurs_Indicator_Process

.. autoprocess:: finch.processes.xclim.hurs_fromdewpoint_Indicator_Process

.. autoprocess:: finch.processes.xclim.ice_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.last_snowfall_Indicator_Process

.. autoprocess:: finch.processes.xclim.last_spring_frost_Indicator_Process

.. autoprocess:: finch.processes.xclim.latitude_temperature_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.liquid_precip_ratio_Indicator_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Indicator_Process

.. autoprocess:: finch.processes.xclim.max_pr_intensity_Indicator_Process

.. autoprocess:: finch.processes.xclim.maximum_consecutive_warm_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.melt_and_precip_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.potential_evapotranspiration_Indicator_Process

.. autoprocess:: finch.processes.xclim.prcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.prlp_Indicator_Process

.. autoprocess:: finch.processes.xclim.prsn_Indicator_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Indicator_Process

.. autoprocess:: finch.processes.xclim.rb_flashiness_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.rx1day_Indicator_Process

.. autoprocess:: finch.processes.xclim.sdii_Indicator_Process

.. autoprocess:: finch.processes.xclim.sea_ice_area_Indicator_Process

.. autoprocess:: finch.processes.xclim.sea_ice_extent_Indicator_Process

.. autoprocess:: finch.processes.xclim.snd_max_doy_Indicator_Process

.. autoprocess:: finch.processes.xclim.snow_cover_duration_Indicator_Process

.. autoprocess:: finch.processes.xclim.snow_depth_Indicator_Process

.. autoprocess:: finch.processes.xclim.snow_melt_we_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.stats_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg10p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg90p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_days_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_days_below_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Indicator_Process

.. autoprocess:: finch.processes.xclim.tg_min_Indicator_Process

.. autoprocess:: finch.processes.xclim.thawing_degree_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn10p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn90p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_days_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Indicator_Process

.. autoprocess:: finch.processes.xclim.tn_min_Indicator_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx10p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx90p_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_days_below_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_max_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_min_Indicator_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Indicator_Process

.. autoprocess:: finch.processes.xclim.warm_and_dry_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.warm_and_wet_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.warm_spell_duration_index_Indicator_Process

.. autoprocess:: finch.processes.xclim.water_budget_Indicator_Process

.. autoprocess:: finch.processes.xclim.wet_prcptot_Indicator_Process

.. autoprocess:: finch.processes.xclim.wetdays_Indicator_Process

.. autoprocess:: finch.processes.xclim.wind_chill_Indicator_Process

.. autoprocess:: finch.processes.xclim.wind_speed_from_vector_Indicator_Process

.. autoprocess:: finch.processes.xclim.wind_vector_from_speed_Indicator_Process

.. autoprocess:: finch.processes.xclim.windy_days_Indicator_Process

.. autoprocess:: finch.processes.xclim.winter_storm_Indicator_Process

Ensemble Processes
------------------
.. autoprocess:: finch.processes.xclim.cdd_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cdd_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cdd_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cold_spell_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cold_spell_duration_index_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.cold_spell_frequency_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cold_spell_frequency_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cold_spell_frequency_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_free_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_free_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.consecutive_frost_free_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cooling_degree_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.corn_heat_units_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.corn_heat_units_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.corn_heat_units_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.cwd_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.cwd_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.cwd_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.degree_days_exceedance_date_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.degree_days_exceedance_date_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.degree_days_exceedance_date_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dlyfrzthw_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dry_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dry_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dry_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dry_spell_frequency_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dry_spell_frequency_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dry_spell_frequency_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dry_spell_total_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dry_spell_total_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dry_spell_total_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dtr_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dtr_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dtr_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dtrmax_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dtrmax_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dtrmax_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.dtrvar_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.effective_growing_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.effective_growing_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.effective_growing_degree_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.etr_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.etr_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.etr_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.first_day_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.first_day_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.first_day_above_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.first_day_below_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.first_day_below_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.first_day_below_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_frequency_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_frequency_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_frequency_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_max_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_max_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_max_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_mean_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_mean_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.freezethaw_spell_mean_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.freezing_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.freezing_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.freezing_degree_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.freshet_start_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.frost_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.frost_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.frost_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_end_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_end_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_end_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_start_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_start_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.frost_free_season_start_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.frost_season_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.frost_season_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.frost_season_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.growing_degree_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.growing_season_end_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.growing_season_end_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.growing_season_end_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.growing_season_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.growing_season_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.growing_season_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.growing_season_start_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.growing_season_start_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.growing_season_start_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_frequency_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_index_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_max_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heat_wave_total_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.heating_degree_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.high_precip_low_temp_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.high_precip_low_temp_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.high_precip_low_temp_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.hot_spell_frequency_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.hot_spell_frequency_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.hot_spell_frequency_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.hot_spell_max_length_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.hot_spell_max_length_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.hot_spell_max_length_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.ice_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.ice_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.ice_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.last_spring_frost_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.last_spring_frost_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.last_spring_frost_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.liquid_precip_ratio_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.liquid_precip_ratio_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.liquid_precip_ratio_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.liquidprcptot_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.max_n_day_precipitation_amount_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.max_pr_intensity_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.max_pr_intensity_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.max_pr_intensity_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.maximum_consecutive_warm_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.maximum_consecutive_warm_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.maximum_consecutive_warm_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.potential_evapotranspiration_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.potential_evapotranspiration_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.potential_evapotranspiration_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.prcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.prcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.prcptot_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.prlp_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.prlp_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.prlp_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.prsn_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.prsn_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.prsn_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.rain_frzgr_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.rx1day_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.rx1day_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.rx1day_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.sdii_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.sdii_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.sdii_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.solidprcptot_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg10p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg10p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg10p_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg90p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg90p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg90p_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg_days_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_days_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_days_above_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg_days_below_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_days_below_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_days_below_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg_max_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_max_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_max_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_mean_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tg_min_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tg_min_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tg_min_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.thawing_degree_days_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.thawing_degree_days_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.thawing_degree_days_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn10p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn10p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn10p_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn90p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn90p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn90p_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn_days_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_days_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_days_above_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_days_below_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn_max_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_max_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_max_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_mean_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tn_min_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tn_min_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tn_min_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tropical_nights_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx10p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx10p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx10p_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx90p_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx90p_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx90p_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_days_above_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx_days_below_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_days_below_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_days_below_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx_max_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_max_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_max_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_mean_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx_min_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_min_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_min_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.tx_tn_days_above_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.warm_spell_duration_index_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.warm_spell_duration_index_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.warm_spell_duration_index_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.water_budget_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.water_budget_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.water_budget_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.wet_prcptot_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.wet_prcptot_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.wet_prcptot_Ensemble_Polygon_Process

.. autoprocess:: finch.processes.xclim.wetdays_Ensemble_Bbox_Process

.. autoprocess:: finch.processes.xclim.wetdays_Ensemble_GridPoint_Process

.. autoprocess:: finch.processes.xclim.wetdays_Ensemble_Polygon_Process

Other Processes
---------------
.. autoprocess:: finch.processes.xclim.AveragePolygonProcess

.. autoprocess:: finch.processes.xclim.BCCAQV2HeatWave

.. autoprocess:: finch.processes.xclim.EmpiricalQuantileMappingProcess

.. autoprocess:: finch.processes.xclim.GeoseriesToNetcdfProcess

.. autoprocess:: finch.processes.xclim.HourlyToDailyProcess

.. autoprocess:: finch.processes.xclim.SubsetBboxBCCAQV2Process

.. autoprocess:: finch.processes.xclim.SubsetBboxDatasetProcess

.. autoprocess:: finch.processes.xclim.SubsetBboxProcess

.. autoprocess:: finch.processes.xclim.SubsetGridPointBCCAQV2Process

.. autoprocess:: finch.processes.xclim.SubsetGridPointDatasetProcess

.. autoprocess:: finch.processes.xclim.SubsetGridPointProcess

.. autoprocess:: finch.processes.xclim.SubsetPolygonProcess
