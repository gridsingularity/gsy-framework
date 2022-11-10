from typing import Callable, Dict, Optional

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.forward_markets.aggregated_ssp import get_aggregated_SSP
from gsy_framework.forward_markets.forward_profile import (
    ForwardTradeProfileGenerator)
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)
from gsy_framework.sim_results.electric_blue.timeseries_base import (
    AssetTimeSeriesBase)
from gsy_framework.utils import round_floats_for_ui, round_prices_to_cents

FORWARD_PRODUCT_TYPES = [
    AvailableMarketTypes.YEAR_FORWARD, AvailableMarketTypes.MONTH_FORWARD,
    AvailableMarketTypes.WEEK_FORWARD, AvailableMarketTypes.DAY_FORWARD,
    AvailableMarketTypes.INTRADAY
]


class AssetVolumeTimeSeries(AssetTimeSeriesBase):
    """This class generates combined volume time series for the whole year for each asset.
    The result would be like this for a monthly resolution for the year 2020:
    {
        DateTime(2020, 1, 1, 0, 0, 0): {
            DateTime(2020, 1, 1, 0, 0, 0): {
                'DAY_FORWARD': {
                    'bought': {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0},
                    'sold': {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0}},
                'MONTH_FORWARD': {
                    'bought': {
                        'energy_kWh': 402.132,
                        'energy_rate': 0.3,
                        'trade_count': 2976,
                        'accumulated_trade_rates': 892.8},
                    'sold': {
                        'energy_kWh': 402.132,
                        'energy_rate': 0.3,
                        'trade_count': 2976,
                        'accumulated_trade_rates': 892.8}},
                'SSP': 201.08320595131318,
                'WEEK_FORWARD': {
                    'bought': {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0},
                    'sold': {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0}},
                'YEAR_FORWARD': {
                    'bought': {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0},
                    'sold': {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0}}},
            DateTime(2020, 2, 1, 0, 0, 0): {...},
            ...
            DateTime(2020, 12, 1, 0, 0, 0): {...},
        },
    }

    Volume time series for each (device_uuid, resolution) pair will be saved in a separate row
    at the DB table. This class may fetch them later (on demand) to update the time series when new
    trades happen on the market.
    """
    def __init__(
            self, asset_uuid: str, asset_peak_kWh: float,
            resolution: AggregationResolution, get_asset_volume_time_series_db: Callable):
        super().__init__(asset_uuid, resolution)
        self.asset_peak_kWh = asset_peak_kWh
        self._trade_profile_generator = ForwardTradeProfileGenerator(self.asset_peak_kWh)
        self.get_asset_volume_time_series_db = get_asset_volume_time_series_db

    def update_time_series(
            self, asset_stats: ForwardDeviceStats, product_type: AvailableMarketTypes):
        self._add_total_energy_bought(asset_stats, product_type)
        self._add_total_energy_sold(asset_stats, product_type)

    def _fetch_asset_time_series_from_db(
            self, year: DateTime) -> Optional[Dict[str, Dict]]:
        """Fetch already saved asset volume time series."""
        return self.get_asset_volume_time_series_db(
            asset_uuid=self.asset_uuid, year=year, resolution=self.resolution)

    def _add_total_energy_bought(
            self, asset_stats: ForwardDeviceStats, product_type: AvailableMarketTypes):
        """Add statistics for the total amount of bought energy."""
        energy_kWh = asset_stats.total_energy_bought
        if energy_kWh <= 0:
            return
        profile = self._trade_profile_generator.generate_trade_profile(
            energy_kWh, asset_stats.time_slot, product_type)
        accumulated_buy_trade_rates = asset_stats.accumulated_buy_trade_rates
        total_buy_trade_count = asset_stats.total_buy_trade_count
        for time_slot, energy in profile.items():
            if energy > 0:
                self._add_to_volume_time_series(
                    time_slot,
                    {
                        "energy_kWh": energy,
                        "accumulated_trade_rates": accumulated_buy_trade_rates,
                        "trade_count": total_buy_trade_count
                    }, product_type, "bought")

    def _add_total_energy_sold(
            self, asset_stats: ForwardDeviceStats, product_type: AvailableMarketTypes):
        """Add statistics for the total amount of sold energy."""
        energy_kWh = asset_stats.total_energy_sold
        if energy_kWh <= 0:
            return
        profile = self._trade_profile_generator.generate_trade_profile(
            energy_kWh, asset_stats.time_slot, product_type
        )
        accumulated_sell_trade_rates = asset_stats.accumulated_sell_trade_rates
        total_sell_trade_count = asset_stats.total_sell_trade_count
        for time_slot, energy in profile.items():
            if energy > 0:
                self._add_to_volume_time_series(
                    time_slot,
                    {
                        "energy_kWh": energy,
                        "accumulated_trade_rates": accumulated_sell_trade_rates,
                        "trade_count": total_sell_trade_count
                    }, product_type, "sold")

    def _add_to_volume_time_series(
            self, time_slot: DateTime, time_slot_info: Dict,
            product_type: AvailableMarketTypes, attribute_name: str):
        """Add time slot value to the correct time slot to asset volume time series."""
        time_slot = self._adapt_time_slot(time_slot)
        year = time_slot.start_of("year")
        volume_time_series = self._get_asset_time_series(year=year)

        # UPDATING energy_kWh, trade_count and energy_rate
        attribute_data = volume_time_series[str(time_slot)][product_type.name][attribute_name]
        attribute_data["energy_kWh"] = round_floats_for_ui(
            attribute_data["energy_kWh"] + time_slot_info["energy_kWh"])

        attribute_data["accumulated_trade_rates"] += time_slot_info["accumulated_trade_rates"]
        attribute_data["trade_count"] += time_slot_info["trade_count"]
        try:
            attribute_data["energy_rate"] = round_prices_to_cents(
                attribute_data["accumulated_trade_rates"] / attribute_data["trade_count"]
            )
        except ZeroDivisionError:
            attribute_data["energy_rate"] = 0.0

        self._asset_time_series_buffer[year] = volume_time_series

    def _generate_time_series(self, year):
        return {
            str(ts): self._get_time_series_template(value)
            for ts, value in self._generate_SSP_time_series(year)}

    def _generate_SSP_time_series(self, year: DateTime):
        """Generate SSP time series for the whole year. The generated time series will then be
        used as a backbone
        to add other statistics."""
        start_time = self._adapt_time_slot(year)
        if start_time < year:
            start_time += self.resolution.duration()

        end_time = self._adapt_time_slot(year.add(years=1))
        if end_time < year.add(years=1):
            end_time += self.resolution.duration()

        return get_aggregated_SSP(
            self.asset_peak_kWh, start_time=start_time, end_time=end_time,
            resolution=self.resolution
        )

    @staticmethod
    def _get_time_series_template(ssp_value: float) -> Dict[str, float]:
        """Generate time slot statistics template for the first time."""
        return {
            "SSP": ssp_value,
            **{
                f"{product_type.name}": {
                    "bought": {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0
                    },
                    "sold": {
                        "energy_kWh": 0.0,
                        "energy_rate": 0.0,
                        "trade_count": 0,
                        "accumulated_trade_rates": 0.0

                    }
                }
                for product_type in FORWARD_PRODUCT_TYPES
            }
        }
