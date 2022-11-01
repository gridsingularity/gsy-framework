from collections import defaultdict
from typing import Dict

from pendulum import DateTime

from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.forward_markets.forward_profile import ALLOWED_MARKET_TYPES
from gsy_framework.sim_results.electric_blue.aggregate_results import (handle_forward_results,
                                                                       ForwardDeviceStats,
                                                                       MARKET_RESOLUTIONS)
from gsy_framework.sim_results.electric_blue.time_series import ForwardDeviceTimeSeries
from gsy_framework.utils import str_to_pendulum_datetime


class ForwardResultsHandler:
    """Calculate all results for each market slot for forward markets."""

    def __init__(self):
        self.forward_market_enabled = True
        self.orders: Dict[
            str, Dict[int, Dict[DateTime, Dict]]] = defaultdict(lambda: defaultdict(dict))
        self.previous_asset_stats = {}
        self.current_asset_stats: Dict[
            int, Dict[DateTime, Dict[str, Dict]]] = defaultdict(lambda: defaultdict(dict))
        self.asset_time_series: Dict[
            int, Dict[int, Dict[DateTime, Dict[str, Dict]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict)))
        self._total_memory_utilization_kb = 0.0

    def update(self, _area_dict: Dict, core_stats: Dict, current_market_slot: str) -> None:
        """
        Update the forward market aggregated results with bids_offers_trades of current slot.
        """
        if not current_market_slot:
            return
        self._buffer_current_asset_stats()
        self._clear_asset_stats()
        for area_uuid, area_result in core_stats.items():
            if "forward_market_stats" not in area_result:
                return

            current_market_dt = str_to_pendulum_datetime(current_market_slot)
            for market_type_value, market_stats in area_result["forward_market_stats"].items():
                market_type = int(market_type_value)
                self._buffer_bids_offers_trades(area_uuid, market_type, market_stats)
                current_results = handle_forward_results(current_market_dt, market_stats)
                self._update_stats_and_time_series(current_results, market_type)
        self._update_memory_utilization()

    def update_from_repr(self, area_representation: Dict):
        """
        Updates the simulation results using area_representation data that arrive from the gsy-web.
        """

    def restore_asset_stats(self, asset_stats):
        """Restore previous asset statistics from the state persisted to the DB."""
        if not self.previous_asset_stats:
            self.previous_asset_stats = asset_stats

    @property
    def all_db_results(self) -> Dict:
        """Get dict with all the results in format that can be saved to the DB."""
        results = {"orders": self.orders, "current_asset_stats": self.current_asset_stats,
                   "asset_time_series": self.asset_time_series, "cumulative_net_energy_flow": {},
                   "cumulative_market_fees": 0.}
        return results

    @property
    def total_memory_utilization_kb(self):
        """Get the total memory allocated by the results."""
        return self._total_memory_utilization_kb

    def _buffer_current_asset_stats(self) -> None:
        self.previous_asset_stats = self.current_asset_stats

    def _clear_asset_stats(self) -> None:
        self.orders.clear()
        self.current_asset_stats = defaultdict(lambda: defaultdict(dict))
        self.asset_time_series.clear()

    def _buffer_bids_offers_trades(self, area_uuid: str, market_type: int,
                                   market_stats: Dict[str, Dict]):
        for time_slot, orders in market_stats.items():
            time_slot_dt = str_to_pendulum_datetime(time_slot)
            self.orders[area_uuid][market_type][time_slot_dt] = {
                order: orders.get(order, []) for order in ("offers", "bids", "trades")}

    def _update_stats_and_time_series(self, forward_results: Dict, market_type_value: int):
        market_type = AvailableMarketTypes(market_type_value)
        for time_slot, asset_results in forward_results.items():
            for asset_uuid, current_asset_stats in asset_results.items():
                if previous_forward_stats := self.previous_asset_stats.get(
                        market_type_value, {}).get(time_slot, {}).get(asset_uuid, {}):
                    previous_asset_stats = ForwardDeviceStats.from_dict(previous_forward_stats)
                    current_asset_stats += previous_asset_stats
                self.current_asset_stats[market_type_value][time_slot][asset_uuid] = \
                    current_asset_stats.to_dict()
                self._generate_asset_time_series(market_type, market_type_value, time_slot,
                                                 asset_uuid, current_asset_stats)

    def _generate_asset_time_series(  # pylint: disable=too-many-arguments
            self, market_type: "AvailableMarketTypes",
            market_type_value: int, time_slot: DateTime, asset_uuid: str,
            current_asset_stats: "ForwardDeviceStats"):
        if market_type not in ALLOWED_MARKET_TYPES:
            # TODO: delete this check, when ForwardTradeProfileGenerator profile generation
            #  functionality will be extended with all forward markets types
            return
        for resolution in MARKET_RESOLUTIONS.get(market_type, []):
            asset_time_series = ForwardDeviceTimeSeries(current_asset_stats, market_type)
            all_time_series_generators = asset_time_series.generate(
                resolution=resolution.duration())
            all_time_series = {k: dict(v) for k, v in all_time_series_generators.items()}
            self.asset_time_series[market_type_value][resolution.value][time_slot][
                asset_uuid] = all_time_series

    def _update_memory_utilization(self) -> None:
        pass
