from collections import defaultdict
from typing import Callable, Dict

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    MARKET_RESOLUTIONS, ForwardDeviceStats, handle_forward_results)
from gsy_framework.sim_results.electric_blue.time_series import (
    ForwardDeviceTimeSeries)
from gsy_framework.sim_results.electric_blue.volume_timeseries import (
    AssetVolumeTimeSeries)
from gsy_framework.utils import str_to_pendulum_datetime


class ForwardResultsHandler:  # pylint: disable=too-many-instance-attributes
    """Calculate all results for each market slot for forward markets."""

    def __init__(self, get_asset_volume_time_series_db: Callable):
        self.forward_market_enabled = True
        self.orders: Dict[
            str, Dict[int, Dict[DateTime, Dict]]] = defaultdict(lambda: defaultdict(dict))
        self.previous_asset_stats = {}
        self.current_asset_stats: Dict[
            int, Dict[DateTime, Dict[str, Dict]]] = defaultdict(lambda: defaultdict(dict))
        self.asset_time_series: Dict[
            int, Dict[int, Dict[DateTime, Dict[str, Dict]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict)))
        self.asset_volume_time_series: Dict[
            str, Dict[AggregationResolution, AssetVolumeTimeSeries]] = {}
        self.get_asset_volume_time_series_db = get_asset_volume_time_series_db
        self._total_memory_utilization_kb = 0.0

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str) -> None:
        """
        Update the forward market aggregated results with bids_offers_trades of current slot.
        """
        if not current_market_slot:
            return
        self._buffer_current_asset_stats()
        self._clear_asset_stats()

        forward_results = self._get_forward_results(core_stats)
        if not forward_results:
            return

        current_market_dt = str_to_pendulum_datetime(current_market_slot)
        for market_type_value, market_stats in forward_results["forward_market_stats"].items():
            market_type = int(market_type_value)
            current_results = handle_forward_results(current_market_dt, market_stats)
            self._update_stats_and_time_series(area_dict, current_results, market_type)
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
                   "cumulative_market_fees": 0.,
                   "asset_volume_time_series": self.asset_volume_time_series}
        return results

    @property
    def total_memory_utilization_kb(self):
        """Get the total memory allocated by the results."""
        return self._total_memory_utilization_kb

    @staticmethod
    def _get_forward_results(core_stats: Dict):
        for area_result in core_stats.values():
            if "forward_market_stats" in area_result:
                return area_result
        return None

    @staticmethod
    def _flatten_area_dict(area_dict: Dict) -> Dict:
        flattened_area_dict = {}
        for child in area_dict["children"]:
            flattened_area_dict[child["uuid"]] = child
        return flattened_area_dict

    def _buffer_current_asset_stats(self) -> None:
        self.previous_asset_stats = self.current_asset_stats

    def _clear_asset_stats(self) -> None:
        self.orders.clear()
        self.current_asset_stats = defaultdict(lambda: defaultdict(dict))
        self.asset_time_series.clear()

    def _buffer_bids_offers_trades(self, market_type: int, forward_results: Dict[DateTime, Dict]):
        for time_slot, asset_results in forward_results.items():
            for area_uuid, asset_result in asset_results.items():
                self.orders[area_uuid][market_type][time_slot] = {
                    "offers": asset_result.open_offers,
                    "bids": asset_result.open_bids,
                    "trades": asset_result.trades
                }

    def _update_stats_and_time_series(
            self, area_dict: Dict, forward_results: Dict, market_type_value: int):
        market_type = AvailableMarketTypes(market_type_value)
        flattened_area = self._flatten_area_dict(area_dict=area_dict)
        self._buffer_bids_offers_trades(market_type_value, forward_results)
        for time_slot, asset_results in forward_results.items():
            for asset_uuid, current_asset_stats in asset_results.items():
                asset_info = flattened_area[asset_uuid]
                # update volume time series
                self._generate_asset_volume_time_series(
                    asset_info, market_type, current_asset_stats)
                # update trade time series
                previous_forward_stats = self.previous_asset_stats.get(
                        market_type_value, {}).get(time_slot, {}).get(asset_uuid, {})
                if previous_forward_stats:
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
        for resolution in MARKET_RESOLUTIONS.get(market_type, []):
            asset_time_series = ForwardDeviceTimeSeries(current_asset_stats, market_type)
            all_time_series_generators = asset_time_series.generate(
                resolution=resolution.duration())
            all_time_series = {k: dict(v) for k, v in all_time_series_generators.items()}
            self.asset_time_series[market_type_value][resolution.value][time_slot][
                asset_uuid] = all_time_series

    def _generate_asset_volume_time_series(
            self, asset_info: Dict, market_type: "AvailableMarketTypes",
            current_asset_stats: "ForwardDeviceStats"):
        """Update asset volume time series in all resolutions."""

        asset_uuid = current_asset_stats.device_uuid
        if asset_uuid not in self.asset_volume_time_series:
            # We assume that for EB, slot length is 1 hour, hence no need for conversion between
            # power and energy
            asset_peak_kwh = (
                asset_info["capacity_kW"] if "capacity_kW" in asset_info
                else asset_info["avg_power_W"] * 1000.0)
            self.asset_volume_time_series[asset_uuid] = {
                resolution: AssetVolumeTimeSeries(
                    asset_uuid=asset_uuid,
                    asset_peak_kWh=asset_peak_kwh,
                    resolution=resolution,
                    get_asset_volume_time_series_db=self.get_asset_volume_time_series_db,
                ) for resolution in list(AggregationResolution)}

        for resolution, time_series in self.asset_volume_time_series[asset_uuid].items():
            time_series.update_time_series(current_asset_stats, market_type)

    def _update_memory_utilization(self) -> None:
        pass
