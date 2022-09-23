from typing import Dict

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.forward_markets.aggregated_profile import (
    get_aggregated_SSP_profile)
from gsy_framework.forward_markets.forward_profile import ForwardTradeProfileGenerator
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)

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

        self._add_total_energy_bought(device_stats, market_type)
        self._add_total_energy_sold(device_stats, market_type)

    def _add_total_energy_bought(
            self, device_stats: ForwardDeviceStats, market_type: AvailableMarketTypes):
        """Add statistics for the total amount of bought energy."""
        energy_kWh = device_stats.total_energy_bought
        if energy_kWh <= 0:
            return
        profile = ForwardTradeProfileGenerator(
            peak_kWh=energy_kWh
        ).generate_trade_profile(
            energy_kWh=energy_kWh,
            market_slot=device_stats.time_slot,
            product_type=market_type
        )
        for time_slot, value in profile.items():
            self._add_to_volume_time_series(time_slot, value, market_type, "bought_kWh")

    def _add_total_energy_sold(
            self, device_stats: ForwardDeviceStats, market_type: AvailableMarketTypes):
        """Add statistics for the total amount of sold energy."""
        energy_kWh = device_stats.total_energy_sold
        if energy_kWh <= 0:
            return
        profile = ForwardTradeProfileGenerator(
            peak_kWh=energy_kWh
        ).generate_trade_profile(
            energy_kWh=energy_kWh,
            market_slot=device_stats.time_slot,
            product_type=market_type
        )
        for time_slot, value in profile.items():
            self._add_to_volume_time_series(time_slot, value, market_type, "sold_kWh")

    def _add_to_volume_time_series(
            self, time_slot: DateTime, value: float,
            market_type: AvailableMarketTypes, attribute_name: str):
        """Add time slot value to the correct time slot to device volume time series."""
        time_slot = self._adapt_time_slot(time_slot)
        volume_time_series = self._get_device_volume_time_series(time_slot.start_of("year"))
        volume_time_series[time_slot][str(market_type)][attribute_name] += value

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
                f"{market_type}": {"bought_kWh": 0, "sold_kWh": 0}
                for market_type in FORWARD_MARKET_TYPES
            }
        }
