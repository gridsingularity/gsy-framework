from collections import defaultdict
from typing import Dict, Iterable, List

from pendulum import DateTime, period

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.forward_markets.aggregated_profile import (
    get_aggregated_SSP_profile)


def fetch_required_market_timeseries(
        device_uuid: str, market_type: AvailableMarketTypes,
        start_time: DateTime, end_time: DateTime, resolution: AggregationResolution) -> Iterable:
    """Determined what time series to fetch from DB with respect to start/end time and
    market_type."""

    if market_type == AvailableMarketTypes.INTRADAY:
        start_time = start_time.set(minute=(start_time.minute // 15) * 15)
        end_time = end_time.set(minute=(start_time.minute // 15) * 15)
        _range = "minutes"
        _range_value = 15
    else:
        _start_of, _range, _range_value = {
            AvailableMarketTypes.YEAR_FORWARD: ("year", "years", 1),
            AvailableMarketTypes.MONTH_FORWARD: ("month", "months", 1),
            AvailableMarketTypes.WEEK_FORWARD: ("weeks", "weeks", 1),
            AvailableMarketTypes.DAY_FORWARD: ("hour", "hours", 1),
        }[market_type]

        start_time = start_time.start_of(_start_of)
        end_time = end_time.start_of(_start_of)

    for time_slot in period(start_time, end_time).range(_range, _range_value):
        yield device_uuid, market_type, time_slot, resolution


class DeviceVolumeTimeSeries:
    """Generate volume time series."""
    def __init__(  # pylint: disable=too-many-arguments
            self, device_uuid: str, device_capacity: float,  start_time: DateTime,
            end_time: DateTime, resolution: AggregationResolution,
            market_types: List[AvailableMarketTypes]):

        self.device_uuid = device_uuid
        self.device_capacity = device_capacity
        self.resolution = resolution

        self.start_time = self._adapt_timeslot(start_time)
        self.end_time = self._adapt_timeslot(end_time)

        self.market_types = market_types

    def generate(self) -> Dict[DateTime, Dict]:
        """Generate volume time series by combining all required markets."""
        result = get_aggregated_SSP_profile(
            self.device_capacity, self.start_time, self.end_time, self.resolution)

        result = {
            time_slot: defaultdict(lambda: 0, {"SSP": energy})
            for time_slot, energy in result
            if time_slot < self.end_time
        }

        for market_type in self.market_types:
            self._handle_market_type(market_type, result)

        return result

    def _adapt_timeslot(self, time_slot: DateTime) -> DateTime:
        """Find the containing time slot of a smaller time slot."""
        if self.resolution == AggregationResolution.RES_15_MINUTES:
            return time_slot.set(minute=(time_slot.minute // 15) * 15)

        start_of = {
            AggregationResolution.RES_1_HOUR: "hour",
            AggregationResolution.RES_1_WEEK: "week",
            AggregationResolution.RES_1_MONTH: "month",
            AggregationResolution.RES_1_YEAR: "year",
        }[self.resolution]

        return time_slot.start_of(start_of)

    def _handle_market_type(self, market_type: AvailableMarketTypes, result: Dict[DateTime, Dict]):
        """Collect required time series and accumulate their time slots with respect to
        market type."""
        for time_series in fetch_required_market_timeseries(
                self.device_uuid, market_type,
                self.start_time, self.end_time, AggregationResolution.RES_15_MINUTES):

            for stat_type in ("matched_sell_orders_kWh", "matched_buy_orders_kWh"):
                for time_slot, value in time_series[stat_type].items():
                    if self.start_time <= time_slot < self.end_time:
                        result[self._adapt_timeslot(time_slot)][
                            f"{market_type}_{stat_type}"] += value
