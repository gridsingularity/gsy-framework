from typing import Callable, Dict

from gsy_e.models.strategy.energy_parameters.energy_params_eb import (
    ForwardTradeProfileGenerator)
from pendulum import DateTime, Duration

from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)


def resample_data(
        timeseries_data: Dict[DateTime, float],
        resolution: Duration, aggregator_fn: Callable) -> Dict:
    """Aggregate data using the specific resolution and aggregator function."""

    result = {}

    sorted_timeslots = sorted(timeseries_data.keys())
    start_time = sorted_timeslots[0]
    next_time = start_time + resolution

    timeslots_to_aggregate = []
    for timeslot in sorted_timeslots:
        if timeslot >= next_time:
            result[timeslots_to_aggregate[0]] = aggregator_fn(
                [timeseries_data[t] for t in timeslots_to_aggregate])
            timeslots_to_aggregate = [timeslot]
            next_time += resolution
        elif timeslot < next_time:
            timeslots_to_aggregate.append(timeslot)

    if timeslots_to_aggregate:
        # aggregate any remaining timeslot in the buffer
        result[timeslots_to_aggregate[0]] = aggregator_fn(
            [timeseries_data[t] for t in timeslots_to_aggregate])

    return result


class ForwardDeviceTimeSeries:
    """Generate time series data using ForwardDeviceStats object."""
    def __init__(
            self, device_stats: ForwardDeviceStats, peak_kWh: float,
            product_type: AvailableMarketTypes):

        self.device_stats = device_stats
        self.product_type = product_type
        self.trade_profile_generator = ForwardTradeProfileGenerator(peak_kWh=peak_kWh)

    def _generate_matched_buy_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for buy trades."""
        if self.device_stats.total_energy_bought <= 0:
            return {}

        matched_buy_profile = self.trade_profile_generator.generate_trade_profile(
            energy_kWh=self.device_stats.total_energy_bought,
            market_slot=DateTime.fromisoformat(self.device_stats.timeslot),
            product_type=self.product_type
        )
        return resample_data(matched_buy_profile, resolution, aggregator_fn=sum)

    def _generate_matched_sell_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for sell trades."""
        if self.device_stats.total_energy_sold <= 0:
            return {}

        matched_sell_profile = self.trade_profile_generator.generate_trade_profile(
            energy_kWh=self.device_stats.total_energy_sold,
            market_slot=DateTime.fromisoformat(self.device_stats.timeslot),
            product_type=self.product_type
        )
        return resample_data(matched_sell_profile, resolution, aggregator_fn=sum)

    def _generate_open_sell_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for all offers."""
        if not self.device_stats.open_offers:
            return {}
        total_offered_energy = sum([offer["energy"] for offer in self.device_stats.open_offers])
        open_sell_profile = self.trade_profile_generator.generate_trade_profile(
            energy_kWh=total_offered_energy,
            market_slot=DateTime.fromisoformat(self.device_stats.timeslot),
            product_type=self.product_type
        )
        return resample_data(open_sell_profile, resolution, aggregator_fn=sum)

    def _generate_open_buy_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for all bids."""
        if not self.device_stats.open_bids:
            return {}
        total_bade_energy = sum([bid["energy"] for bid in self.device_stats.open_bids])
        open_buy_profile = self.trade_profile_generator.generate_trade_profile(
            energy_kWh=total_bade_energy,
            market_slot=DateTime.fromisoformat(self.device_stats.timeslot),
            product_type=self.product_type
        )
        return resample_data(open_buy_profile, resolution, aggregator_fn=sum)

    def _generate_all_buy_orders_kWh(self, resolution: Duration) -> Dict:
        """Generate time series for all (bids + buy trades)."""
        total_bade_energy = sum([bid["energy"] for bid in self.device_stats.open_bids])
        all_buy_orders_kWh = self.device_stats.total_energy_bought + total_bade_energy

        if all_buy_orders_kWh <= 0:
            return {}

        all_buy_profile = self.trade_profile_generator.generate_trade_profile(
            energy_kWh=all_buy_orders_kWh,
            market_slot=DateTime.fromisoformat(self.device_stats.timeslot),
            product_type=self.product_type
        )
        return resample_data(all_buy_profile, resolution, aggregator_fn=sum)

    def _generate_all_sell_orders(self, resolution):
        """Generate time series for all (offers + sell trades)."""
        total_offered_energy = sum([offer["energy"] for offer in self.device_stats.open_offers])
        all_sell_orders_kWh = self.device_stats.total_energy_sold + total_offered_energy

        if all_sell_orders_kWh <= 0:
            return {}

        all_sell_profile = self.trade_profile_generator.generate_trade_profile(
            energy_kWh=all_sell_orders_kWh,
            market_slot=DateTime.fromisoformat(self.device_stats.timeslot),
            product_type=self.product_type
        )
        return resample_data(all_sell_profile, resolution, aggregator_fn=sum)

    def generate(self, resolution: Duration):
        """Generate all time series."""
        return {
            "matched_buy_orders_kWh": self._generate_matched_buy_orders_kWh(resolution),
            "matched_sell_orders_kWh": self._generate_matched_sell_orders_kWh(resolution),
            "open_sell_orders_kWh": self._generate_open_sell_orders_kWh(resolution),
            "open_buy_orders_kWh": self._generate_matched_buy_orders_kWh(resolution),
            "all_buy_orders_KWh": self._generate_all_buy_orders_kWh(resolution),
            "all_sell_orders_kWh": self._generate_all_sell_orders(resolution)
        }
