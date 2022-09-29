from typing import Dict, Union

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.forward_markets.aggregated_ssp import (
    get_aggregated_SSP_profile)
from gsy_framework.forward_markets.forward_profile import (
    ForwardTradeProfileGenerator)
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)

FORWARD_MARKET_TYPES = [
    AvailableMarketTypes.YEAR_FORWARD, AvailableMarketTypes.MONTH_FORWARD,
    AvailableMarketTypes.WEEK_FORWARD, AvailableMarketTypes.DAY_FORWARD,
]

# a dictionary showing the start of time slot for each resolution.
START_OF = {
    AggregationResolution.RES_1_HOUR: "hour",
    AggregationResolution.RES_1_WEEK: "week",
    AggregationResolution.RES_1_MONTH: "month",
    AggregationResolution.RES_1_YEAR: "year",
}


class AssetVolumeTimeSeries:
    """This class generates combined volume time series for the whole year for each asset.
    The result would be like this for a monthly resolution for the year 2020:
    {
        DateTime(2020, 1, 1, 0, 0, 0): {
            DateTime(2020, 1, 1, 0, 0, 0): {
                "SSP": 1005.4160297565659,
                "YEAR_FORWARD": {
                    "bought_kWh": 201.08320595131318,
                    "sold_kWh": 201.08320595131318,
                },
                "MONTH_FORWARD": {
                    "bought_kWh": 201.08320595131318,
                    "sold_kWh": 201.08320595131318,
                },
                "WEEK_FORWARD": {
                    "bought_kWh": 32.432775153437625,
                    "sold_kWh": 32.432775153437625,
                },
                "DAY_FORWARD": {
                    "bought_kWh": 6.486555030687522,
                    "sold_kWh": 6.486555030687522,
                },
            },
            DateTime(2020, 2, 1, 0, 0, 0): {...},
            ...
            DateTime(2020, 12, 1, 0, 0, 0): {...},
        },
    }
    """
    def __init__(
            self, asset_uuid: str, asset_capacity: float,
            resolution: AggregationResolution):

        self.asset_uuid = asset_uuid
        self.asset_capacity = asset_capacity
        self.resolution = resolution

        self._asset_volume_time_series_buffer: Dict[DateTime, Dict] = {}

    def add(self, asset_stats: ForwardDeviceStats, market_type: AvailableMarketTypes):
        """Add asset time series to asset volume time series."""

        self._add_total_energy_bought(asset_stats, market_type)
        self._add_total_energy_sold(asset_stats, market_type)

    def save_time_series(self):
        """Save asset volume time series in the DB."""
        # TODO: should be implemented.
        raise NotImplementedError()

    def _add_total_energy_bought(
            self, asset_stats: ForwardDeviceStats, market_type: AvailableMarketTypes):
        """Add statistics for the total amount of bought energy."""
        energy_kWh = asset_stats.total_energy_bought
        if energy_kWh <= 0:
            return
        profile = ForwardTradeProfileGenerator(self.asset_capacity).generate_trade_profile(
            energy_kWh, asset_stats.time_slot, market_type)
        for time_slot, value in profile.items():
            self._add_to_volume_time_series(time_slot, value, market_type, "bought_kWh")

    def _add_total_energy_sold(
            self, asset_stats: ForwardDeviceStats, market_type: AvailableMarketTypes):
        """Add statistics for the total amount of sold energy."""
        energy_kWh = asset_stats.total_energy_sold
        if energy_kWh <= 0:
            return
        profile = ForwardTradeProfileGenerator(self.asset_capacity).generate_trade_profile(
            energy_kWh, asset_stats.time_slot, market_type
        )
        for time_slot, value in profile.items():
            self._add_to_volume_time_series(time_slot, value, market_type, "sold_kWh")

    def _add_to_volume_time_series(
            self, time_slot: DateTime, value: float,
            market_type: AvailableMarketTypes, attribute_name: str):
        """Add time slot value to the correct time slot to asset volume time series."""
        time_slot = self._adapt_time_slot(time_slot)
        volume_time_series = self._get_asset_volume_time_series(time_slot.start_of("year"))
        volume_time_series[time_slot][str(market_type)][attribute_name] += value

    def _adapt_time_slot(self, time_slot: DateTime) -> DateTime:
        """Find the containing time slot of the smaller time slot."""
        if self.resolution == AggregationResolution.RES_15_MINUTES:
            return time_slot.set(minute=(time_slot.minute // 15) * 15)
        return time_slot.start_of(START_OF[self.resolution])

    def _get_asset_volume_time_series(self, time_slot):
        """Return asset volume time series for the required time slot.
        If not found in the buffer, it tries fetching it from DB.
        If not found in the DB, it will generate a new one for the whole year."""
        if time_slot in self._asset_volume_time_series_buffer:
            time_series = self._asset_volume_time_series_buffer[time_slot]
        else:
            time_series = self._fetch_asset_volume_time_series_from_db(time_slot)
            if time_series is None:
                time_series = {
                    ts: self._get_time_series_template(value)
                    for ts, value in self._generate_asset_volume_time_series(time_slot)}
            self._asset_volume_time_series_buffer[time_slot] = time_series
        return time_series

    def _fetch_asset_volume_time_series_from_db(
            self, time_slot: DateTime) -> Union[Dict[DateTime, Dict], None]:
        """Fetch already saved asset volume time series."""
        # TODO: should be implemented.
        return None

    def _generate_asset_volume_time_series(self, time_slot: DateTime):
        """Generate asset volume time series for the whole year."""
        start_time = self._adapt_time_slot(time_slot)
        if start_time < time_slot:
            start_time += self.resolution.duration()

        end_time = self._adapt_time_slot(time_slot.add(years=1))
        if end_time < time_slot.add(years=1):
            end_time += self.resolution.duration()

        return get_aggregated_SSP_profile(
            self.asset_capacity, start_time=start_time, end_time=end_time,
            resolution=self.resolution
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
