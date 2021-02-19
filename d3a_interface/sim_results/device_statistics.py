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

from typing import Dict

from d3a_interface.utils import create_or_update_subdict, limit_float_precision
from d3a_interface.sim_results import is_load_node_type, is_pv_node_type, \
    is_prosumer_node_type, is_bulk_power_producer, is_buffer_node_type, \
    is_finite_power_plant_node_type
from d3a_interface.sim_results.results_abc import ResultsBaseClass

FILL_VALUE = None


class DeviceStatistics(ResultsBaseClass):

    def __init__(self, should_export_plots):
        self.device_stats_dict = {}
        self.current_stats_dict = {}
        self.current_stats_time_str = {}
        self.should_export_plots = should_export_plots

    @staticmethod
    def _calc_min_max_from_sim_dict(subdict: Dict, key: str):

        min_trade_stats_daily = {}
        max_trade_stats_daily = {}
        indict = subdict[key]

        trade_stats_daily = dict((k, []) for k, v in indict.items())
        for time, value in indict.items():
            value = [] if value is None else value
            value = [value] if not isinstance(value, list) else value
            trade_stats_daily[time] += value

        for time_str, value in trade_stats_daily.items():
            min_trade_stats_daily[time_str] = limit_float_precision(min(value)) \
                if len(value) > 0 else FILL_VALUE
            max_trade_stats_daily[time_str] = limit_float_precision(max(value)) \
                if len(value) > 0 else FILL_VALUE

        min_trade_stats = dict((time, min_trade_stats_daily[time])
                               for time in indict.keys())
        max_trade_stats = dict((time, max_trade_stats_daily[time])
                               for time in indict.keys())

        create_or_update_subdict(subdict, f"min_{key}", min_trade_stats)
        create_or_update_subdict(subdict, f"max_{key}", max_trade_stats)

    @classmethod
    def _device_price_stats(cls, area_dict: Dict, subdict: Dict, core_stats, current_market_slot):
        key_name = "trade_price_eur"
        if core_stats[area_dict['uuid']] == {}:
            return
        area_core_trades = core_stats[area_dict['uuid']].get('trades', [])
        trade_price_list = []
        for t in area_core_trades:
            if t['seller'] == area_dict['name'] or t['buyer'] == area_dict['name']:
                trade_price_list.append(t['energy_rate'] / 100.0)
        if trade_price_list:
            create_or_update_subdict(
                subdict, key_name,
                {current_market_slot: trade_price_list})
        else:
            create_or_update_subdict(
                subdict, key_name,
                {current_market_slot: FILL_VALUE})

        cls._calc_min_max_from_sim_dict(subdict, key_name)

    @classmethod
    def _device_energy_stats(cls, area_dict: Dict, subdict: Dict, core_stats: Dict,
                             current_market_slot):
        if is_bulk_power_producer(area_dict) or is_buffer_node_type(area_dict) or \
                is_finite_power_plant_node_type(area_dict):
            cls.calculate_stats_for_infinite_bus(area_dict, subdict, core_stats,
                                                 current_market_slot)
        else:
            cls.calculate_stats_for_device(area_dict, subdict, core_stats, current_market_slot)

    @classmethod
    def calculate_stats_for_device(cls, area_dict, subdict, core_stats, current_market_slot):
        key_name = "trade_energy_kWh"
        if core_stats[area_dict['uuid']] == {}:
            return
        area_core_trades = core_stats[area_dict['uuid']].get('trades', [])

        traded_energy = 0
        for t in area_core_trades:
            if t['seller'] == area_dict['name']:
                traded_energy -= t['energy']
            if t['buyer'] == area_dict['name']:
                traded_energy += t['energy']

        create_or_update_subdict(
            subdict, key_name,
            {current_market_slot: traded_energy})
        cls._calc_min_max_from_sim_dict(subdict, key_name)

    @classmethod
    def calculate_stats_for_infinite_bus(cls, area_dict, subdict, core_stats, current_market_slot):
        sold_key_name = "sold_trade_energy_kWh"
        bought_key_name = "bought_trade_energy_kWh"
        sold_traded_energy = 0
        bought_traded_energy = 0
        if core_stats[area_dict['uuid']] == {}:
            return
        area_core_trades = core_stats[area_dict['uuid']].get('trades', [])

        for t in area_core_trades:
            if t['seller'] == area_dict['name']:
                sold_traded_energy += t['energy']
            if t['buyer'] == area_dict['name']:
                bought_traded_energy += t['energy']
        create_or_update_subdict(
            subdict, sold_key_name,
            {current_market_slot: sold_traded_energy})
        cls._calc_min_max_from_sim_dict(subdict, sold_key_name)
        create_or_update_subdict(
            subdict, bought_key_name,
            {current_market_slot: bought_traded_energy})
        cls._calc_min_max_from_sim_dict(subdict, bought_key_name)

    @classmethod
    def _pv_production_stats(cls, area_dict: Dict, subdict: Dict, core_stats=None,
                             current_market_slot=None):
        if core_stats is None:
            core_stats = {}
        key_name = "pv_production_kWh"
        if core_stats[area_dict['uuid']] == {}:
            return

        create_or_update_subdict(
            subdict, key_name,
            {current_market_slot: core_stats[area_dict["uuid"]][key_name]})

        cls._calc_min_max_from_sim_dict(subdict, key_name)

    @classmethod
    def _soc_stats(cls, area_dict: Dict, subdict: Dict, core_stats=None, current_market_slot=None):
        if core_stats is None:
            core_stats = {}
        key_name = "soc_history_%"
        if core_stats[area_dict['uuid']] == {}:
            return
        create_or_update_subdict(
            subdict, key_name,
            {current_market_slot: core_stats[area_dict["uuid"]][key_name]})

        cls._calc_min_max_from_sim_dict(subdict, key_name)

    @classmethod
    def _load_profile_stats(cls, area_dict: Dict, subdict: Dict, core_stats=None,
                            current_market_slot=None):
        if core_stats is None:
            core_stats = {}
        key_name = "load_profile_kWh"
        if core_stats[area_dict['uuid']] == {}:
            return
        create_or_update_subdict(
            subdict, key_name,
            {current_market_slot: core_stats[area_dict["uuid"]][key_name]}
        )

        cls._calc_min_max_from_sim_dict(subdict, key_name)

    def update(self, area_result_dict=None, core_stats=None, current_market_slot=None):
        if not self._validate_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return
        if self.should_export_plots:
            self.gather_device_statistics(
                area_result_dict, self.device_stats_dict, {}, core_stats,
                current_market_slot)
        else:
            self.gather_device_statistics(
                area_result_dict, {}, self.current_stats_dict, core_stats,
                current_market_slot)

    @classmethod
    def gather_device_statistics(cls, area_dict: Dict, subdict: Dict,
                                 flat_result_dict: Dict,
                                 core_stats=None, current_market_slot=None):
        if core_stats is None:
            core_stats = {}
        for child in area_dict['children']:
            if child['name'] not in subdict.keys():
                subdict.update({child['name']: {}})
            if child['children'] == [] and core_stats != {}:
                cls._gather_device_statistics(
                    child, subdict[child['name']], flat_result_dict,
                    core_stats, current_market_slot)
            else:
                cls.gather_device_statistics(
                    child, subdict[child['name']], flat_result_dict,
                    core_stats, current_market_slot)

    @classmethod
    def _gather_device_statistics(cls, area_dict: Dict, subdict: Dict,
                                  flat_result_dict: Dict,
                                  core_stats=None, current_market_slot=None):
        if core_stats is None or core_stats.get(area_dict['uuid'], {}) == {}:
            return

        if area_dict['type'] != "area_dict":
            cls._device_price_stats(area_dict, subdict, core_stats, current_market_slot)
            cls._device_energy_stats(area_dict, subdict, core_stats, current_market_slot)

        if is_pv_node_type(area_dict):
            cls._pv_production_stats(area_dict, subdict, core_stats, current_market_slot)

        elif is_prosumer_node_type(area_dict):
            cls._soc_stats(area_dict, subdict, core_stats, current_market_slot)

        elif is_load_node_type(area_dict):
            cls._load_profile_stats(area_dict, subdict, core_stats, current_market_slot)

        elif area_dict['type'] == "FinitePowerPlant":
            create_or_update_subdict(
                subdict, "production_kWh",
                {current_market_slot: core_stats[area_dict["uuid"]]["production_kWh"]}
            )
            cls._calc_min_max_from_sim_dict(subdict, "production_kWh")

        flat_result_dict[area_dict["uuid"]] = subdict.copy()

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
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
