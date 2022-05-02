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
from datetime import timedelta, date  # NOQA
from typing import Dict, List
from gsy_framework.sim_results.area_throughput_stats import AreaThroughputStats
from gsy_framework.sim_results.energy_trade_profile import EnergyTradeProfile
from gsy_framework.sim_results.market_price_energy_day import MarketPriceEnergyDay
from gsy_framework.sim_results.asset_statistics import AssetStatistics
from gsy_framework.sim_results.market_summary_info import MarketSummaryInfo


REQUESTED_FIELDS_LIST = [
    "price_energy_day", "asset_statistics",
    "energy_trade_profile", "area_throughput",
    "market_summary"
]


REQUESTED_FIELDS_CLASS_MAP = {
    "price_energy_day": MarketPriceEnergyDay,
    # TODO: remove `device_statistics`; It's only kept for backward compatibility.
    "device_statistics": AssetStatistics,
    "asset_statistics": AssetStatistics,
    "energy_trade_profile": EnergyTradeProfile,
    "area_throughput": AreaThroughputStats,
    "market_summary": MarketSummaryInfo
}


def merge_last_market_results_to_global(
        market_results: Dict, global_results: Dict,
        slot_list_ui_format: List = None, requested_fields: List = None
):
    if requested_fields is None:
        requested_fields = REQUESTED_FIELDS_LIST

    for field in requested_fields:
        global_results[field] = REQUESTED_FIELDS_CLASS_MAP[field].merge_results_to_global(
            market_results[field], global_results[field], slot_list_ui_format
        )

    # TODO: remove `device_statistics`; It's only kept for backward compatibility.
    if "asset_statistics" in requested_fields:
        global_results['device_statistics'] = global_results['asset_statistics']

    return global_results
