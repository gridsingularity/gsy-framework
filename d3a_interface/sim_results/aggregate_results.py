"""
Copyright 2018 Grid Singularity
This file is part of D3A.

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
from datetime import timedelta, date  # NOQA
from typing import Dict, List
from d3a_interface.utils import generate_market_slot_list_from_config, \
    convert_datetime_to_str_in_list


class UnmatchedLoadsHelpers:

    @classmethod
    def _merge_base_area_unmatched_loads(cls, accumulated_results: Dict,
                                         current_results: Dict, area: str):
        """
        Recurses over all children (target areas) of base area and calculates the unmatched
        loads for each
        :param accumulated_results: stores the merged unmatched load results, changes by reference
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :param area: area of the accumulated unmatched loads
        :return: None
        """
        if area not in current_results or current_results[area] is None:
            accumulated_results[area] = None
            return
        for target, target_value in current_results[area].items():
            if target not in accumulated_results[area]:
                accumulated_results[area][target] = deepcopy(target_value)
            else:
                if target == 'type':
                    continue
                elif target == 'unmatched_loads':
                    cls._copy_accumulated_unmatched_loads(
                        accumulated_results, current_results, area
                    )
                else:
                    cls._merge_target_area_unmatched_loads(
                        accumulated_results, current_results, area, target
                    )

    @classmethod
    def _merge_target_area_unmatched_loads(cls, accumulated_results: Dict,
                                           current_results: Dict, area: str, target: str):
        """
        Merges the unmatched loads and unmatched times for a base area and a target area.
        :param accumulated_results: stores the merged unmatched load results, changes by reference
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :param area: area of the accumulated unmatched loads
        :param target: target area of the accumulated unmatched loads
        :return: None
        """
        target_ul = accumulated_results[area][target]['unmatched_loads']
        current_ul = current_results[area][target]['unmatched_loads']
        for timestamp, ts_value in current_ul.items():
            if timestamp not in target_ul:
                target_ul[timestamp] = deepcopy(ts_value)
            else:
                if 'unmatched_times' not in current_ul[timestamp]:
                    continue
                if 'unmatched_times' not in target_ul[timestamp]:
                    target_ul[timestamp]['unmatched_times'] = {}
                for device, time_list in current_ul[timestamp]['unmatched_times'].items():
                    if device not in target_ul[timestamp]['unmatched_times']:
                        target_ul[timestamp]['unmatched_times'][device] = deepcopy(time_list)
                    else:
                        for ts in time_list:
                            if ts not in target_ul[timestamp]['unmatched_times'][device]:
                                target_ul[timestamp]['unmatched_times'][device].append(ts)

                unm_count = 0
                for _, hours in target_ul[timestamp]['unmatched_times'].items():
                    unm_count += len(hours)

                    target_ul[timestamp]['unmatched_count'] = unm_count

    @classmethod
    def _copy_accumulated_unmatched_loads(cls, accumulated_results: Dict,
                                          current_results: Dict, area: str):
        """
        Copies the accumulated results from the market results to the incremental results
        :param accumulated_results: stores the merged unmatched load results, changes by reference
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :param area: area of the accumulated unmatched loads
        :return: None
        """
        for timestamp, ts_value in current_results[area]['unmatched_loads'].items():
            if timestamp not in accumulated_results[area]['unmatched_loads']:
                accumulated_results[area]['unmatched_loads'][timestamp] = deepcopy(ts_value)

    @classmethod
    def accumulate_current_market_results(cls, accumulated_results: Dict, current_results: Dict):
        """
        Method which starts the merging of the current market unmatched loads with the
        existing unmatched loads (_unmatched_loads_incremental)
        :param accumulated_results: return value, stores the merged unmatched load results
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :return: accumulated_results
        """
        for base_area, target_results in current_results.items():
            if base_area not in accumulated_results:
                accumulated_results[base_area] = deepcopy(target_results)
            else:
                cls._merge_base_area_unmatched_loads(
                    accumulated_results, current_results, base_area
                )
        return accumulated_results


def merge_unmatched_load_results_to_global(market_ul: Dict, global_ul: Dict):
    if not global_ul:
        global_ul = market_ul
        return global_ul
    return UnmatchedLoadsHelpers.accumulate_current_market_results(global_ul, market_ul)


def merge_price_energy_day_results_to_global(market_pe: Dict, global_pe: Dict):
    if not global_pe:
        global_pe = market_pe
        return global_pe
    for area_uuid in market_pe:
        if area_uuid not in global_pe:
            global_pe[area_uuid] = deepcopy(market_pe[area_uuid])
        else:
            global_pe[area_uuid]["price-energy-day"].extend(
                market_pe[area_uuid]["price-energy-day"])
    return global_pe


def merge_device_statistics_results_to_global(market_device: Dict, global_device: Dict):
    if not global_device:
        global_device = market_device
        return global_device
    for area_uuid in market_device:
        if area_uuid not in global_device:
            global_device[area_uuid] = market_device[area_uuid]
        else:
            for stat in market_device[area_uuid]:
                if stat not in global_device[area_uuid]:
                    global_device[area_uuid][stat] = market_device[area_uuid][stat]
                else:
                    global_device[area_uuid][stat].update(market_device[area_uuid][stat])
    return global_device


def merge_energy_trade_profile_to_global(market_trade: Dict, global_trade: Dict, slot_list: List):
    if not global_trade:
        global_trade = market_trade
        return global_trade
    for area_uuid in market_trade:
        if area_uuid not in global_trade or global_trade[area_uuid] == {}:
            global_trade[area_uuid] = {"sold_energy": {}, "bought_energy": {}}
        for sold_bought in market_trade[area_uuid]:
            for target_area in market_trade[area_uuid][sold_bought]:
                if target_area not in global_trade[area_uuid][sold_bought]:
                    global_trade[area_uuid][sold_bought][target_area] = {}
                for source_area in market_trade[area_uuid][sold_bought][target_area]:
                    if source_area not in global_trade[area_uuid][sold_bought][target_area]:
                        global_trade[area_uuid][sold_bought][target_area][source_area] = \
                            {i: 0 for i in slot_list}
                    global_trade[area_uuid][sold_bought][target_area][source_area].update(
                        market_trade[area_uuid][sold_bought][target_area][source_area]
                    )
    return global_trade


def merge_area_throughput_results_to_global(market_trade: Dict, global_trade: Dict):
    if not global_trade:
        global_trade = market_trade
        return global_trade
    for area_uuid in market_trade:
        if area_uuid not in global_trade or global_trade[area_uuid] == {}:
            global_trade[area_uuid] = {}
        for time_slot in market_trade[area_uuid]:
            global_trade[area_uuid][time_slot] = market_trade[area_uuid][time_slot]
    return global_trade


def merge_last_market_results_to_global(
        market_results: Dict, global_results: Dict,
        sim_duration: timedelta, start_date: date, market_count: int, slot_length: timedelta
):
    slot_list_ui_format = convert_datetime_to_str_in_list(
        generate_market_slot_list_from_config(sim_duration, start_date, market_count, slot_length),
        ui_format=True)
    global_results["unmatched_loads"] = merge_unmatched_load_results_to_global(
        market_results["unmatched_loads"], global_results["unmatched_loads"])
    global_results["price_energy_day"] = merge_price_energy_day_results_to_global(
        market_results["price_energy_day"], global_results["price_energy_day"])
    global_results["device_statistics"] = merge_device_statistics_results_to_global(
        market_results["device_statistics"], global_results["device_statistics"])
    global_results["energy_trade_profile"] = merge_energy_trade_profile_to_global(
        market_results["energy_trade_profile"],
        global_results["energy_trade_profile"], slot_list_ui_format
    )
    global_results["area_throughput"] = merge_area_throughput_results_to_global(
        market_results["area_throughput"], global_results["area_throughput"]
    )
    return global_results
