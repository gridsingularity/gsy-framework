from typing import Dict

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.forward_markets.aggregated_profile import (
    get_aggregated_SSP_profile)
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)
from gsy_framework.sim_results.electric_blue.time_series import (
    ForwardDeviceTimeSeries)

FORWARD_MARKET_TYPES = [
    AvailableMarketTypes.YEAR_FORWARD, AvailableMarketTypes.MONTH_FORWARD,
    AvailableMarketTypes.WEEK_FORWARD, AvailableMarketTypes.DAY_FORWARD,
    AvailableMarketTypes.INTRADAY
]

# a dictionary showing the start of time slot for each resolution.
START_OF = {
    AggregationResolution.RES_1_HOUR: "hour",
    AggregationResolution.RES_1_WEEK: "week",
    AggregationResolution.RES_1_MONTH: "month",
    AggregationResolution.RES_1_YEAR: "year",
}


class DeviceVolumeTimeSeries:
    """This class generated combined volume time series for the whole year for each device.
    """
    def __init__(
            self, device_uuid: str, device_capacity: float,
            resolution: AggregationResolution):

        self.device_uuid = device_uuid
        self.device_capacity = device_capacity
        self.resolution = resolution

        self._device_volume_time_series_buffer: Dict[DateTime, Dict] = {}

    def add(self, device_stats: ForwardDeviceStats, market_type: AvailableMarketTypes):
        """Add device time series to device volume time series."""
        device_time_series = ForwardDeviceTimeSeries(device_stats, market_type).generate(
            AggregationResolution.RES_15_MINUTES.duration())

        for time_slot, value in device_time_series["matched_sell_orders_kWh"].items():
            self._add_to_volume_time_series(time_slot, value, f"{market_type}_sold")

        for time_slot, value in device_time_series["matched_buy_orders_kWh"].items():
            self._add_to_volume_time_series(time_slot, value, f"{market_type}_bought")

    def _add_to_volume_time_series(self, time_slot: DateTime, value: float, attribute_name: str):
        """Add time slot value to the correct time slot to device volume time series."""
        time_slot = self._adapt_time_slot(time_slot)
        volume_time_series = self._get_device_volume_time_series(time_slot.start_of("year"))
        volume_time_series[time_slot][attribute_name] += value

    def _adapt_time_slot(self, time_slot: DateTime) -> DateTime:
        """Find the containing time slot of the smaller time slot."""
        if self.resolution == AggregationResolution.RES_15_MINUTES:
            return time_slot.set(minute=(time_slot.minute // 15) * 15)
        return time_slot.start_of(START_OF[self.resolution])

    def _get_device_volume_time_series(self, time_slot):
        """Return device volume time series for the required time slot.
        If not found in the buffer, it tries fetching it from DB.
        If not found in the DB, it will generate a new one for the whole year."""
        if time_slot in self._device_volume_time_series_buffer:
            time_series = self._device_volume_time_series_buffer[time_slot]
        else:
            time_series = self._fetch_device_volume_time_series_from_db(time_slot)
            if time_series is None:
                time_series = {
                    ts: self._get_time_series_template(value)
                    for ts, value in self._generate_device_volume_time_series(time_slot)}
            self._device_volume_time_series_buffer[time_slot] = time_series
        return time_series

    def _fetch_device_volume_time_series_from_db(self, time_slot: DateTime):
        # TODO: should be implemented by Kamil.
        raise NotImplementedError()

    def _generate_device_volume_time_series(self, time_slot: DateTime):
        """Generate device volume time series for the whole year."""
        return get_aggregated_SSP_profile(
            self.device_capacity, time_slot,
            time_slot.add(years=1), resolution=self.resolution
        )

    @staticmethod
    def _get_time_series_template(ssp_value: float) -> Dict[str, float]:
        """Generate time slot statistics template for the first time."""
        return {
            "SSP": ssp_value,
            **{
                f"{market_type}_{order_type}": 0
                for market_type in FORWARD_MARKET_TYPES
                for order_type in ["sold", "bought"]
            }
        }
