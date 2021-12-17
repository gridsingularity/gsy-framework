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
from collections import OrderedDict
from typing import Dict
from copy import deepcopy

from gsy_framework.utils import round_floats_for_ui, \
    convert_pendulum_to_str_in_dict, key_in_dict_and_not_none
from gsy_framework.sim_results.results_abc import ResultsBaseClass


class MarketPriceEnergyDay(ResultsBaseClass):
    def __init__(self, should_export_plots):
        self._price_energy_day = {}
        self.csv_output = {}
        self.redis_output = {}
        self.should_export_plots = should_export_plots

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([
            self.csv_output, self.redis_output, self._price_energy_day
        ])

    @classmethod
    def gather_trade_rates(cls, area_dict, core_stats, current_market_slot, price_lists):
        if area_dict['children'] == []:
            return price_lists

        cls.gather_rates_one_market(area_dict, core_stats, current_market_slot, price_lists)

        for child in area_dict['children']:
            price_lists = cls.gather_trade_rates(child, core_stats, current_market_slot,
                                                 price_lists)

        return price_lists

    @classmethod
    def gather_rates_one_market(cls, area_dict, core_stats, current_market_slot, price_lists):
        if area_dict['uuid'] not in price_lists:
            price_lists[area_dict['uuid']] = OrderedDict()
        if current_market_slot not in price_lists[area_dict['uuid']].keys():
            price_lists[area_dict['uuid']][current_market_slot] = []
        trade_rates = [
            # Convert from cents to euro
            t['energy_rate'] / 100.0
            for t in core_stats.get(area_dict['uuid'], {}).get('trades', [])
        ]
        price_lists[area_dict['uuid']][current_market_slot].extend(trade_rates)

    def update(self, area_result_dict=None, core_stats=None, current_market_slot=None):
        if not self._has_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return
        current_price_lists = self.gather_trade_rates(
            area_result_dict, core_stats, current_market_slot, {}
        )
        price_energy_redis_output = {}
        self._convert_output_format(current_price_lists, price_energy_redis_output,
                                    core_stats)
        if self.should_export_plots:
            self.calculate_csv_output(area_result_dict, price_energy_redis_output)
        else:
            self.redis_output = price_energy_redis_output

    def calculate_csv_output(self, area_dict, price_energy_redis_output):
        if not price_energy_redis_output.get(area_dict['uuid'], {}).get('price-energy-day', []):
            return
        if area_dict['name'] not in self.csv_output:
            self.csv_output[area_dict['name']] = {
                "price-currency": "Euros",
                "load-unit": "kWh",
                "price-energy-day": []
            }
        self.csv_output[area_dict['name']]["price-energy-day"].\
            append(price_energy_redis_output[area_dict['uuid']]['price-energy-day'])
        for child in area_dict['children']:
            self.calculate_csv_output(child, price_energy_redis_output)

    @staticmethod
    def _convert_output_format(price_energy, redis_output, core_stats):
        for node_uuid, trade_rates in price_energy.items():
            if node_uuid not in redis_output:
                redis_output[node_uuid] = {
                    "price-currency": "Euros",
                    "load-unit": "kWh",
                    "price-energy-day": []
                }
            redis_output[node_uuid]["price-energy-day"] = [
                {
                    "time": time_slot,
                    "min_price": round_floats_for_ui(min(trades) if len(trades) > 0 else 0),
                    "max_price": round_floats_for_ui(max(trades) if len(trades) > 0 else 0),
                } for time_slot, trades in trade_rates.items()
            ]

            area_core_stats = core_stats.get(node_uuid, {})
            fee = area_core_stats['grid_fee_constant'] / 100 \
                if key_in_dict_and_not_none(area_core_stats, 'grid_fee_constant') else None

            redis_output[node_uuid]["price-energy-day"][0].update({"grid_fee_constant": fee})

    @staticmethod
    def merge_results_to_global(market_pe: Dict, global_pe: Dict, *_):
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

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        pass

    @property
    def raw_results(self):
        return self.csv_output

    @property
    def ui_formatted_results(self):
        return convert_pendulum_to_str_in_dict(self.redis_output, {})
