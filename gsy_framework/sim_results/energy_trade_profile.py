"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from copy import deepcopy
from typing import Dict, List

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE
from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import (
    round_floats_for_ui, add_or_create_key,
    ui_str_to_pendulum_datetime, convert_pendulum_to_str_in_dict,
    datetime_str_to_ui_formatted_datetime_str, area_name_from_area_or_ma_name)

traded_energy_profile_example = {
    "area_uuid1": {
        "sold_energy": {
            "trade_seller1": {
                "accumulated": {
                    "time_slot1": 0,
                    "time_slot2": 0
                },
                "trade_buyer1": {
                    "time_slot1": 0,
                    "time_slot2": 0
                },
                "trade_buyer2": {
                    "time_slot1": 0,
                    "time_slot2": 0
                }
            }
        },
        "bought_energy": {
            "trade_buyer1": {
                "accumulated": {
                    "time_slot1": 0,
                    "time_slot2": 0
                },
                "trade_seller1": {
                    "time_slot1": 0
                }
            }
        }
    }
}


class EnergyTradeProfile(ResultsBaseClass):
    """
    Total energy traded for each market and energy asset and their penalty for not trading
    their required energy.
    """
    def __init__(self, should_export_plots: bool):
        self.traded_energy_profile: traded_energy_profile_example = {}
        self.traded_energy_current: traded_energy_profile_example = {}
        self.should_export_plots: bool = should_export_plots

    def update(self, area_result_dict=None, core_stats=None, current_market_slot=None):
        if not self._has_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return
        current_market_slot = datetime_str_to_ui_formatted_datetime_str(current_market_slot)
        self.traded_energy_current = {}
        self._populate_area_children_data(area_result_dict, core_stats, current_market_slot)

    def _populate_area_children_data(self, area_result_dict, core_stats, current_market_slot):
        if area_result_dict.get("children") is not None:
            for child in area_result_dict["children"]:
                self._populate_area_children_data(child, core_stats, current_market_slot)
            if self.should_export_plots:
                self._update_sold_bought_energy(area_result_dict, core_stats, current_market_slot)
            else:
                self._update_current_energy_trade_profile(
                    area_result_dict, core_stats, current_market_slot
                )

    def _update_current_energy_trade_profile(self, area_result_dict, core_stats,
                                             current_market_slot):
        if current_market_slot is not None:
            self.traded_energy_current[area_result_dict["uuid"]] = {
                "sold_energy": {}, "bought_energy": {}
            }
            self._calculate_devices_sold_bought_energy(
                self.traded_energy_current[area_result_dict["uuid"]],
                area_result_dict,
                core_stats,
                current_market_slot
            )
            self._round_energy_trade_profile(self.traded_energy_current)

    def _update_sold_bought_energy(self, area_result_dict, core_stats, current_market_slot):
        if current_market_slot is not None:
            area_name = area_result_dict["name"]
            self.traded_energy_current[area_name] = {"sold_energy": {}, "bought_energy": {}}
            self._calculate_devices_sold_bought_energy(
                self.traded_energy_current[area_name], area_result_dict,
                core_stats, current_market_slot)

            traded_energy_current_name = {area_name: self.traded_energy_current[area_name]}
            self.traded_energy_profile = self.merge_results_to_global(
                traded_energy_current_name, self.traded_energy_profile,
                [current_market_slot])

    @staticmethod
    def _calculate_devices_sold_bought_energy(res_dict, area_result_dict, core_stats,
                                              current_market_slot):
        if area_result_dict["uuid"] not in core_stats:
            return
        if core_stats[area_result_dict["uuid"]] == {}:
            return
        area_core_trades = EnergyTradeProfile._get_trades_from_core_stats(
            core_stats, area_result_dict["uuid"])
        for trade in area_core_trades:
            trade_seller = area_name_from_area_or_ma_name(trade["seller"])
            trade_buyer = area_name_from_area_or_ma_name(trade["buyer"])

            if trade_seller not in res_dict["sold_energy"]:
                res_dict["sold_energy"][trade_seller] = {"accumulated": {}}
            if trade_buyer not in res_dict["sold_energy"][trade_seller]:
                res_dict["sold_energy"][trade_seller][trade_buyer] = {}
            trade_energy = trade["energy"]
            if trade_energy > FLOATING_POINT_TOLERANCE:
                add_or_create_key(res_dict["sold_energy"][trade_seller]["accumulated"],
                                  current_market_slot, trade_energy)
                add_or_create_key(res_dict["sold_energy"][trade_seller][trade_buyer],
                                  current_market_slot, trade_energy)
            if trade_buyer not in res_dict["bought_energy"]:
                res_dict["bought_energy"][trade_buyer] = {"accumulated": {}}
            if trade_seller not in res_dict["bought_energy"][trade_buyer]:
                res_dict["bought_energy"][trade_buyer][trade_seller] = {}
            if trade_energy > FLOATING_POINT_TOLERANCE:
                add_or_create_key(res_dict["bought_energy"][trade_buyer]["accumulated"],
                                  current_market_slot, trade_energy)
                add_or_create_key(res_dict["bought_energy"][trade_buyer][trade_seller],
                                  current_market_slot, trade_energy)

    @staticmethod
    def _round_energy_trade_profile(energy_profile: Dict):
        for area_energy_mapping in energy_profile.values():
            for sold_bought in ("sold_energy", "bought_energy"):
                if sold_bought not in area_energy_mapping:
                    continue
                for trades_mapping in area_energy_mapping[sold_bought].values():
                    for trades_timestamps in trades_mapping.values():
                        for timestamp in trades_timestamps.keys():
                            trades_timestamps[timestamp] = round_floats_for_ui(
                                trades_timestamps[timestamp])
        return energy_profile

    @staticmethod
    def _add_sold_bought_lists(trades_profile: Dict):
        for trades_mapping in trades_profile.values():
            for sold_bought in ("sold_energy", "bought_energy"):
                trades_mapping[sold_bought + "_lists"] = (
                    dict((key, {}) for key in trades_mapping[sold_bought].keys()))
                for node in trades_mapping[sold_bought].keys():
                    trades_mapping[sold_bought + "_lists"][node]["slot"] = (
                        list(trades_mapping[sold_bought][node]["accumulated"].keys()))
                    trades_mapping[sold_bought + "_lists"][node]["energy"] = (
                        list(trades_mapping[sold_bought][node]["accumulated"].values()))

    @staticmethod
    def _convert_timestamp_strings_to_datetimes(profile: Dict) -> Dict:
        out_dict = {}
        for key in profile.keys():
            out_dict[key] = {}
            for sold_bought in ("sold_energy", "bought_energy"):
                if sold_bought not in profile[key]:
                    continue
                out_dict[key][sold_bought] = {}
                for dev in profile[key][sold_bought].keys():
                    out_dict[key][sold_bought][dev] = {}
                    for target in profile[key][sold_bought][dev].keys():
                        out_dict[key][sold_bought][dev][target] = {}
                        for timestamp_str in profile[key][sold_bought][dev][target].keys():
                            datetime_obj = ui_str_to_pendulum_datetime(timestamp_str)
                            out_dict[key][sold_bought][dev][target][datetime_obj] = (
                                profile[key][sold_bought][dev][target][timestamp_str])
        return out_dict

    @staticmethod
    def merge_results_to_global(market_results: Dict, global_results: Dict, slot_list: List):
        if not global_results:
            global_trade = market_results
            return global_trade
        for area_uuid in market_results:
            if global_results.get(area_uuid, {}) == {}:
                global_results[area_uuid] = {"sold_energy": {}, "bought_energy": {}}
            for sold_bought in market_results[area_uuid]:
                for target_area in market_results[area_uuid][sold_bought]:
                    if target_area not in global_results[area_uuid][sold_bought]:
                        global_results[area_uuid][sold_bought][target_area] = {}
                    for source_area in market_results[area_uuid][sold_bought][target_area]:
                        if source_area not in global_results[area_uuid][sold_bought][target_area]:
                            global_results[area_uuid][sold_bought][target_area][source_area] = (
                                {i: 0 for i in slot_list})
                        global_results[area_uuid][sold_bought][target_area][source_area].update(
                            market_results[area_uuid][sold_bought][target_area][source_area]
                        )
        return global_results

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        pass

    @property
    def plot_results(self) -> Dict:
        """Return the energy trade profile data to be plotted."""
        traded_profile_for_plot = self._convert_timestamp_strings_to_datetimes(
                deepcopy(self.traded_energy_profile)
        )
        self._add_sold_bought_lists(traded_profile_for_plot)
        return traded_profile_for_plot

    @property
    def raw_results(self) -> str:
        return convert_pendulum_to_str_in_dict(
            self.traded_energy_profile, {}, ui_format=True)

    @property
    def ui_formatted_results(self) -> str:
        return convert_pendulum_to_str_in_dict(
            self.traded_energy_current, {}, ui_format=True)

    def memory_allocation_size_kb(self) -> float:
        return self._calculate_memory_allocated_by_objects([
            self.traded_energy_current, self.traded_energy_profile
        ])
