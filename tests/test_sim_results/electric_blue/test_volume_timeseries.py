from typing import List

import pytest
from pendulum import DateTime

from gsy_framework.enums import AggregationResolution
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)
from gsy_framework.sim_results.electric_blue.volume_timeseries import (
    FORWARD_MARKET_TYPES, AssetVolumeTimeSeries)
from tests.forward_markets.test_aggregated_profile import (
    get_sum_of_ssp_profile_range_values as sum_of_energy)


@pytest.fixture
def forward_time_series():
    """Return a generator that produces ForwardDeviceStats objects for testing purposes."""
    def func():
        for market_type in FORWARD_MARKET_TYPES:
            yield market_type, ForwardDeviceStats(
                device_uuid="UUID",
                time_slot=DateTime(2020, 1, 1),
                current_time_slot=DateTime(2020, 1, 1),
                total_energy_sold=1,
                total_energy_bought=1)
    return func()


class TestAssetVolumeTimeSeries:
    @staticmethod
    def check_time_slot_pairs(time_slots: List, resolution: AggregationResolution):
        """Check the returned value of _adapt_time_slot is equal to the expected value."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=1, resolution=resolution)

        for expected, actual in time_slots:
            assert expected == volume_time_series._adapt_time_slot(actual)

    @staticmethod
    def check_time_slots_year(volume_time_series: AssetVolumeTimeSeries):
        """Check all timeslots of a given year belong to that year."""
        for year in volume_time_series._asset_volume_time_series_buffer:
            for year_within in volume_time_series._asset_volume_time_series_buffer[year]:
                assert year_within.startswith(str(year.year))

    def test_adapt_time_slot_for_15_minute_resolution(self):
        self.check_time_slot_pairs([
            (DateTime(2020, 1, 1, 0, 0), DateTime(2020, 1, 1, 0, 10)),
            (DateTime(2020, 1, 1, 0, 45), DateTime(2020, 1, 1, 0, 50)),
            (DateTime(2020, 1, 1, 2, 0), DateTime(2020, 1, 1, 2, 0)),
            (DateTime(2020, 1, 1, 2, 15), DateTime(2020, 1, 1, 2, 15)),
        ], resolution=AggregationResolution.RES_15_MINUTES)

    def test_adapt_time_slot_for_1_hour_resolution(self):
        self.check_time_slot_pairs([
            (DateTime(2020, 1, 1, 0, 0), DateTime(2020, 1, 1, 0, 0)),
            (DateTime(2020, 1, 1, 0, 0), DateTime(2020, 1, 1, 0, 20)),
            (DateTime(2020, 1, 1, 2, 0), DateTime(2020, 1, 1, 2, 30)),
        ], resolution=AggregationResolution.RES_1_HOUR)

    def test_adapt_time_slot_for_1_week_resolution(self):
        self.check_time_slot_pairs([
            (DateTime(2020, 1, 1, 0, 0).start_of("week"), DateTime(2020, 1, 1, 0, 0)),
            (DateTime(2020, 2, 1, 0, 20).start_of("week"), DateTime(2020, 2, 1, 0, 20)),
        ], resolution=AggregationResolution.RES_1_WEEK)

    def test_adapt_time_slot_for_1_month_resolution(self):
        self.check_time_slot_pairs([
            (DateTime(2020, 1, 1, 0, 0).start_of("month"), DateTime(2020, 1, 1, 0, 0)),
            (DateTime(2020, 2, 29, 0, 20).start_of("month"), DateTime(2020, 2, 29, 0, 20)),
        ], resolution=AggregationResolution.RES_1_MONTH)

    def test_adapt_time_slot_for_1_year_resolution(self):
        self.check_time_slot_pairs([
            (DateTime(2020, 1, 1, 0, 0).start_of("month"), DateTime(2020, 1, 1, 0, 0)),
            (DateTime(2020, 2, 29, 0, 20).start_of("year"), DateTime(2020, 2, 29, 0, 20)),
        ], resolution=AggregationResolution.RES_1_YEAR)

    def test_add_asset_time_series_for_1_year_resolution(self, forward_time_series):
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5, resolution=AggregationResolution.RES_1_YEAR)

        for market_type, asset_stats in forward_time_series:
            volume_time_series.update_volume_time_series(asset_stats, market_type)

        self.check_time_slots_year(volume_time_series)
        assert volume_time_series._asset_volume_time_series_buffer == {
            DateTime(2020, 1, 1, 0, 0, 0): {
                str(DateTime(2020, 1, 1, 0, 0, 0)): {
                    "SSP": 36164.701938689024,
                    "YEAR_FORWARD": {
                        "bought_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("year"),
                            1
                        ),
                        "sold_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("year"),
                            1
                        )},
                    "MONTH_FORWARD": {
                        "bought_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("month"),
                            1
                        ),
                        "sold_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("month"),
                            1
                        )
                    },
                    "WEEK_FORWARD": {
                        "bought_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("week"),
                            1
                        ),
                        "sold_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("week"),
                            1
                        )},
                    "DAY_FORWARD": {"bought_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("day"),
                            1
                        ), "sold_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0),
                            DateTime(2020, 1, 1, 0, 0, 0).end_of("day"),
                            1
                        )}}},
            DateTime(2019, 1, 1, 0, 0, 0): {
                str(DateTime(2019, 1, 1, 0, 0, 0)): {
                    "SSP": 36100.3496802018,
                    "YEAR_FORWARD": {"bought_kWh": 0, "sold_kWh": 0},
                    "MONTH_FORWARD": {"bought_kWh": 0, "sold_kWh": 0},
                    "WEEK_FORWARD": {
                        "bought_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0).start_of("week"),
                            DateTime(2020, 1, 1, 0, 0, 0),
                            1
                        ),
                        "sold_kWh": sum_of_energy(
                            DateTime(2020, 1, 1, 0, 0, 0).start_of("week"),
                            DateTime(2020, 1, 1, 0, 0, 0),
                            1
                        )
                    },
                    "DAY_FORWARD": {"bought_kWh": 0, "sold_kWh": 0}}}}

    def test_add_asset_time_series_for_1_month_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 1-month resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5, resolution=AggregationResolution.RES_1_MONTH)

        try:
            for market_type, asset_stats in forward_time_series:
                volume_time_series.update_volume_time_series(asset_stats, market_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)

    def test_add_asset_time_series_for_1_week_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 1-week resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5, resolution=AggregationResolution.RES_1_WEEK)

        try:
            for market_type, asset_stats in forward_time_series:
                volume_time_series.update_volume_time_series(asset_stats, market_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)

    def test_add_asset_time_series_for_1_hour_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 1-hour resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5, resolution=AggregationResolution.RES_1_HOUR)

        try:
            for market_type, asset_stats in forward_time_series:
                volume_time_series.update_volume_time_series(asset_stats, market_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)

    def test_add_asset_time_series_for_15_minutes_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 15-minutes resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5, resolution=AggregationResolution.RES_15_MINUTES)

        try:
            for market_type, asset_stats in forward_time_series:
                volume_time_series.update_volume_time_series(asset_stats, market_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)
