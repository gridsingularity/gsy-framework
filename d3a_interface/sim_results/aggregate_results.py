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
from datetime import timedelta, date  # NOQA
from typing import Dict, List
from d3a_interface.utils import generate_market_slot_list_from_config, \
    convert_datetime_to_str_in_list
from d3a_interface.sim_results.area_throughput_stats import AreaThroughputStats
from d3a_interface.sim_results.energy_trade_profile import EnergyTradeProfile
from d3a_interface.sim_results.market_price_energy_day import MarketPriceEnergyDay
from d3a_interface.sim_results.export_unmatched_loads import MarketUnmatchedLoads
from d3a_interface.sim_results.device_statistics import DeviceStatistics


REQUESTED_FIELDS_LIST = ["unmatched_loads", "price_energy_day", "device_statistics",
                         "energy_trade_profile", "area_throughput"]


REQUESTED_FIELDS_CLASS_MAP = {
    "unmatched_loads": MarketUnmatchedLoads,
    "price_energy_day": MarketPriceEnergyDay,
    "device_statistics": DeviceStatistics,
    "energy_trade_profile": EnergyTradeProfile,
    "area_throughput": AreaThroughputStats
}


def merge_last_market_results_to_global(
        market_results: Dict, global_results: Dict,
        sim_duration: timedelta, start_date: date, market_count: int, slot_length: timedelta,
        requested_fields: List = None
):
    if requested_fields is None:
        requested_fields = REQUESTED_FIELDS_LIST

    slot_list_ui_format = convert_datetime_to_str_in_list(
        generate_market_slot_list_from_config(sim_duration, start_date, market_count, slot_length),
        ui_format=True)

    for field in requested_fields:
        global_results[field] = REQUESTED_FIELDS_CLASS_MAP[field].merge_results_to_global(
            market_results[field], global_results[field], slot_list_ui_format
        )

    return global_results
