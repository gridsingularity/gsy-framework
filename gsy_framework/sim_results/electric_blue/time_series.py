from typing import Callable, Dict

from pendulum import DateTime, Duration

from gsy_framework.constants_limits import DATE_TIME_FORMAT
from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.forward_markets.forward_profile import (
    ForwardTradeProfileGenerator)
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)


def resample_data(
        timeseries_data: Dict[DateTime, float],
        resolution: Duration, aggregator_fn: Callable) -> Dict:
    """Aggregate data using the specified resolution and aggregator function."""

    result = {}

    sorted_time_slots = sorted(timeseries_data.keys())
    start_time = sorted_time_slots[0]
    next_time = start_time + resolution

    time_slots_to_aggregate = []
    for time_slot in sorted_time_slots:
        if time_slot >= next_time:
            time_slot_str = time_slots_to_aggregate[0].format(DATE_TIME_FORMAT)
            result[time_slot_str] = aggregator_fn(
                [timeseries_data[t] for t in time_slots_to_aggregate])
            time_slots_to_aggregate = [time_slot]
            next_time += resolution
        elif time_slot < next_time:
            time_slots_to_aggregate.append(time_slot)

    if time_slots_to_aggregate:
        # aggregate any remaining time_slots in the buffer
        time_slot_str = time_slots_to_aggregate[0].format(DATE_TIME_FORMAT)
        result[time_slot_str] = aggregator_fn(
            [timeseries_data[t] for t in time_slots_to_aggregate])

    return result


class ForwardDeviceTimeSeries:
    """Generate time series data using ForwardDeviceStats object."""
    def __init__(
            self, device_stats: ForwardDeviceStats, product_type: AvailableMarketTypes):

        self.device_stats = device_stats
        self.product_type = product_type

    def generate(self, resolution: Duration):
        """Generate all time series."""
        return {
            "matched_buy_orders_kWh": self._generate_matched_buy_orders_kWh(resolution),
            "matched_sell_orders_kWh": self._generate_matched_sell_orders_kWh(resolution),
            "open_sell_orders_kWh": self._generate_open_sell_orders_kWh(resolution),
            "open_buy_orders_kWh": self._generate_open_buy_orders_kWh(resolution),
            "all_buy_orders_KWh": self._generate_all_buy_orders_kWh(resolution),
            "all_sell_orders_kWh": self._generate_all_sell_orders(resolution)
        }

    def _generate_resampled_profile(self, energy_kWh: float, resolution: Duration) -> Dict:
        """Generate profile and resample it afterwards."""
        if energy_kWh <= 0:
            return {}

        profile = ForwardTradeProfileGenerator(
            peak_kWh=energy_kWh
        ).generate_trade_profile(
            energy_kWh=energy_kWh,
            market_slot=self.device_stats.time_slot,
            product_type=self.product_type
        )
        return resample_data(profile, resolution=resolution, aggregator_fn=sum)

    def _generate_matched_buy_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for buy trades."""
        return self._generate_resampled_profile(
            self.device_stats.total_energy_bought,
            resolution
        )

    def _generate_matched_sell_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for sell trades."""
        return self._generate_resampled_profile(
            self.device_stats.total_energy_sold,
            resolution
        )

    def _generate_open_sell_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for all offers."""
        total_offered_energy = sum([offer["energy"] for offer in self.device_stats.open_offers])
        return self._generate_resampled_profile(
            total_offered_energy,
            resolution
        )

    def _generate_open_buy_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for all bids."""
        total_bade_energy = sum([bid["energy"] for bid in self.device_stats.open_bids])
        return self._generate_resampled_profile(
            total_bade_energy,
            resolution
        )

    def _generate_all_buy_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for all (bids + buy trades)."""
        total_bade_energy = sum([bid["energy"] for bid in self.device_stats.open_bids])
        all_buy_orders_kWh = self.device_stats.total_energy_bought + total_bade_energy
        return self._generate_resampled_profile(
            all_buy_orders_kWh,
            resolution
        )

    def _generate_all_sell_orders(self, resolution):
        """Generate time series for all (offers + sell trades)."""
        total_offered_energy = sum([offer["energy"] for offer in self.device_stats.open_offers])
        all_sell_orders_kWh = self.device_stats.total_energy_sold + total_offered_energy
        return self._generate_resampled_profile(
            all_sell_orders_kWh,
            resolution
        )
