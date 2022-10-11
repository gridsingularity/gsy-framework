from collections import defaultdict
from typing import Dict

from pendulum import from_format, Duration

from gsy_framework.constants_limits import DATE_TIME_FORMAT
from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.forward_markets.forward_profile import ALLOWED_MARKET_TYPES
from gsy_framework.sim_results.electric_blue.aggregate_results import (handle_forward_results,
                                                                       ForwardDeviceStats,
                                                                       MARKET_RESOLUTIONS)
from gsy_framework.sim_results.electric_blue.time_series import ForwardDeviceTimeSeries


class ForwardResultsHandler:
    """Calculate all results for each market slot for forward markets."""

    def __init__(self, slot_length: Duration):
        self.forward_market_enabled = True
        self.slot_length = slot_length
        self.previous_device_stats = defaultdict(lambda: defaultdict(dict))
        self._generate_device_statistics()
        self._total_memory_utilization_kb = 0.0

    # pylint: disable=unused-argument
    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str) -> None:
        """
        Update the forward market aggregated results with bids_offers_trades of current slot.
        """
        for area_uuid, area_result in core_stats.items():
            if "forward_market_stats" not in area_result:
                return

            current_market_dt = from_format(current_market, DATE_TIME_FORMAT) if (
                current_market := current_market_slot) else ""
            for market_type_value, market_stats in area_result["forward_market_stats"].items():
                self._get_bids_offers_trades(area_uuid, market_type_value, market_stats)
                current_results = handle_forward_results(current_market_dt, market_stats)
                self._update_stats_and_time_series(current_results, market_type_value)
        self._update_memory_utilization()

    def update_from_repr(self, area_representation: Dict):
        """
        Updates the simulation results using area_representation data that arrive from the d3a-web.
        """

    @property
    def all_db_results(self) -> Dict:
        """Get dict with all the results in format that can be saved to the DB."""
        results = {"bids_offers_trades": self.bids_offers_trades}
        if self.current_device_stats:
            results["current_device_stats"] = self.current_device_stats
        if self.device_time_series:
            results["device_time_series"] = self.device_time_series
        self._generate_device_statistics()
        results["cumulative_net_energy_flow"] = {}
        results["cumulative_market_fees"] = 0.
        return results

    @property
    def total_memory_utilization_kb(self):
        """Get the total memory allocated by the results."""
        return self._total_memory_utilization_kb

    def _generate_device_statistics(self):
        self.bids_offers_trades = defaultdict(lambda: defaultdict(dict))
        self.current_device_stats = defaultdict(lambda: defaultdict(dict))
        self.device_time_series = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    def _get_bids_offers_trades(self, area_uuid: str, market_type: int, market_stats: Dict):
        for time_slot, orders in market_stats.items():
            self.bids_offers_trades[area_uuid][market_type][time_slot] = \
                {order: orders.get(order, []) for order in ("offers", "bids", "trades")}

    def _update_stats_and_time_series(self, forward_results: Dict, market_type_value: str):
        market_type = AvailableMarketTypes(int(market_type_value))
        for time_slot, device_results in forward_results.items():
            for device_uuid, current_device_stats in device_results.items():
                if previous_forward_stats := self.previous_device_stats.get(
                        market_type_value, {}).get(time_slot, {}).get(device_uuid, {}):
                    previous_device_stats = ForwardDeviceStats(**previous_forward_stats)
                    current_device_stats += previous_device_stats
                self.current_device_stats[market_type_value][time_slot][device_uuid] = \
                    current_device_stats.to_dict()
                if market_type not in ALLOWED_MARKET_TYPES:
                    # TODO: delete this check, when ForwardTradeProfileGenerator profile generation
                    #  functionality will be extend with all forward markets types
                    continue
                for resolution in MARKET_RESOLUTIONS.get(market_type, []):
                    device_time_series = ForwardDeviceTimeSeries(current_device_stats, market_type)
                    all_time_series_generators = device_time_series.generate(
                        resolution=resolution.duration())
                    all_time_series = {k: dict(v) for k, v in all_time_series_generators.items()}
                    self.device_time_series[market_type_value][resolution.value][time_slot][
                        device_uuid] = all_time_series

    def _update_memory_utilization(self) -> None:
        pass
