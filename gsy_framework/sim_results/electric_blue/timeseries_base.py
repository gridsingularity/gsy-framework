import abc
from typing import Dict, Optional

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)

# a dictionary showing the start of time slot for each resolution.
START_OF = {
    AggregationResolution.RES_1_HOUR: "hour",
    AggregationResolution.RES_1_WEEK: "week",
    AggregationResolution.RES_1_MONTH: "month",
    AggregationResolution.RES_1_YEAR: "year",
}


class AssetTimeSeriesBase(abc.ABC):
    """Base class for calculating different timeseries for forward markets."""
    def __init__(self, asset_uuid: str, resolution: AggregationResolution):
        self.asset_uuid = asset_uuid
        self.resolution = resolution
        self.asset_time_series_buffer: Dict[int, Dict] = {}

    @abc.abstractmethod
    def update_time_series(
            self, asset_stats: ForwardDeviceStats, product_type: AvailableMarketTypes):
        """Update asset volume time series with the current asset stats: stats from the last 15
        minutes."""

    @abc.abstractmethod
    def _fetch_asset_time_series_from_db(
            self, year: int) -> Optional[Dict[str, Dict]]:
        """Fetch already saved asset volume time series."""

    @abc.abstractmethod
    def _generate_time_series(self, year):
        """Generate time series for the asset."""

    def _adapt_time_slot(self, time_slot: DateTime) -> DateTime:
        """Adapt given time_slot with time series resolution."""
        if self.resolution == AggregationResolution.RES_15_MINUTES:
            return time_slot.set(minute=(time_slot.minute // 15) * 15)
        return time_slot.start_of(START_OF[self.resolution])

    def _get_asset_time_series(self, year: DateTime) -> Dict[str, Dict]:
        """Return asset volume time series for the required year.
        If not found in the buffer, it tries fetching it from DB.
        If not found in the DB, it will generate a new one for the whole year."""
        if year.year in self.asset_time_series_buffer:
            time_series = self.asset_time_series_buffer[year.year]
        else:
            time_series = self._fetch_asset_time_series_from_db(year.year)
            if time_series is None:
                time_series = self._generate_time_series(year)
        return time_series
