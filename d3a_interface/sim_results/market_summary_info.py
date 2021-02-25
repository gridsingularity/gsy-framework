from typing import Dict
from statistics import mean
from d3a_interface.utils import key_in_dict_and_not_none
from d3a_interface.sim_results.results_abc import ResultsBaseClass
from d3a_interface.sim_results import is_trade_external


class MarketSummaryInfo(ResultsBaseClass):

    def __init__(self, should_export_plots):
        self._should_export_plots = should_export_plots
        self._market_summary = {}

    @staticmethod
    def merge_results_to_global(market_results: Dict, global_results: Dict, *_):
        if not global_results:
            global_results = {
                area_uuid: [results]
                for area_uuid, results in market_results.items()
                if results
            }
            return global_results
        for area_uuid in market_results:
            if area_uuid not in global_results:
                global_results[area_uuid] = [market_results[area_uuid]]
            else:
                global_results[area_uuid].append(market_results[area_uuid])
        return global_results

    def update(self, area_result_dict, core_stats, current_market_slot):
        if not self._has_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return
        if self._should_export_plots:
            # Do not run this
            return
        self._update_results(area_result_dict, core_stats, current_market_slot)

    def _update_results(self, area_dict, core_stats, current_market_slot):
        if not key_in_dict_and_not_none(area_dict, 'children'):
            return
        self._calculate_market_summary_for_area(area_dict, core_stats, current_market_slot)
        for child in area_dict['children']:
            self._update_results(child, core_stats, current_market_slot)

    def _calculate_market_summary_for_area(self, area_dict, core_stats, current_market_slot):
        price_list = []
        volume_kWh = 0.0
        external_traded_volume_kWh = 0.0
        child_names = [c["name"] for c in area_dict["children"]]
        for trade in core_stats.get(area_dict['uuid'], {}).get('trades', []):
            price_list.append(trade["energy_rate"])
            volume_kWh += trade["energy"]
            if is_trade_external(trade, area_dict["name"], child_names):
                external_traded_volume_kWh += trade["energy"]

        self._market_summary[area_dict["uuid"]] = {
            "average_energy_rate": mean(price_list) if price_list else None,
            "external_traded_volume": external_traded_volume_kWh,
            "traded_volume": volume_kWh,
            "timestamp": current_market_slot
        }

    def restore_area_results_state(self, area_uuid, last_known_state_data):
        pass

    @property
    def raw_results(self):
        return self._market_summary
