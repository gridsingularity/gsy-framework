from typing import List
from unittest.mock import Mock, call, patch

import pytest
from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)
from gsy_framework.sim_results.electric_blue.volume_timeseries import (
    FORWARD_PRODUCT_TYPES, AssetVolumeTimeSeries)


def fake_get_asset_volume_time_series_db(*_args, **_kwargs):
    """Fake function that returns None when called by the asset volume time series."""
    return None


@pytest.fixture
def forward_time_series():
    """Return a generator that produces ForwardDeviceStats objects for testing purposes."""
    def func():
        for product_type in FORWARD_PRODUCT_TYPES:
            yield product_type, ForwardDeviceStats(
                device_uuid="UUID",
                time_slot=DateTime(2020, 1, 1),
                current_time_slot=DateTime(2020, 1, 1),
                total_energy_sold=1,
                total_energy_bought=1,
                total_spent_eur=30,
                total_earned_eur=45
            )
    return func()


class TestAssetVolumeTimeSeries:
    @staticmethod
    def check_time_slot_pairs(time_slots: List, resolution: AggregationResolution):
        """Check the returned value of _adapt_time_slot is equal to the expected value."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=1, resolution=resolution,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        for expected, actual in time_slots:
            assert expected == volume_time_series._adapt_time_slot(actual)

    @staticmethod
    def check_time_slots_year(volume_time_series: AssetVolumeTimeSeries):
        """Check all timeslots of a given year belong to that year."""
        for year in volume_time_series.asset_time_series_buffer:
            for year_within in volume_time_series.asset_time_series_buffer[year]:
                assert year_within.startswith(str(year))

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

    @patch.object(AssetVolumeTimeSeries, "_add_total_energy_bought")
    @patch.object(AssetVolumeTimeSeries, "_add_total_energy_sold")
    def test_update_time_series_method_works(
            self, add_total_energy_bought_mock, add_total_energy_sold_mock):
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_YEAR,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        asset_stats = ForwardDeviceStats("UUID", DateTime(2020, 1, 1), DateTime(2020, 1, 1))
        volume_time_series.update_time_series(asset_stats, AvailableMarketTypes.WEEK_FORWARD)

        self.check_time_slots_year(volume_time_series)
        add_total_energy_bought_mock.assert_called_once()
        add_total_energy_sold_mock.assert_called_once()

    @staticmethod
    def test_add_total_energy_bought_works_correctly():
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_WEEK,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        profile = {f"time_slot_{i}": 0.5 for i in range(3)}
        with patch.object(
                volume_time_series._trade_profile_generator,
                "generate_trade_profile", Mock(return_value=profile)) as profile_generator_mock:
            # profile generator should not be called when total_energy_bought is <= 0
            asset_stats = ForwardDeviceStats("UUID", DateTime(2020, 1, 1), DateTime(2020, 1, 1))
            volume_time_series._add_total_energy_bought(
                asset_stats, AvailableMarketTypes.YEAR_FORWARD)
            profile_generator_mock.assert_not_called()

            # profile generator should be called when total_energy_bought is > 0
            with patch.object(
                volume_time_series, "_add_to_volume_time_series"
            ) as add_to_volume_time_series_mock:
                asset_stats = ForwardDeviceStats(
                    "UUID", DateTime(2020, 1, 1), DateTime(2020, 1, 1), total_energy_bought=2,
                    total_spent_eur=0.6)
                volume_time_series._add_total_energy_bought(
                    asset_stats, AvailableMarketTypes.YEAR_FORWARD)
                profile_generator_mock.assert_called_once_with(
                    asset_stats.total_energy_bought, asset_stats.time_slot,
                    AvailableMarketTypes.YEAR_FORWARD
                )
                expected_calls = []
                for time_slot, energy in profile.items():
                    expected_calls.append(
                        call.do_work(
                            time_slot,
                            {
                                "energy_kWh": energy,
                                "trade_count": asset_stats.total_buy_trade_count,
                                "accumulated_trade_rates": asset_stats.accumulated_buy_trade_rates
                            },
                            AvailableMarketTypes.YEAR_FORWARD, "bought"
                        )
                    )
                assert add_to_volume_time_series_mock.call_count == 3
                add_to_volume_time_series_mock.assert_has_calls(expected_calls)

    @staticmethod
    def test_add_total_energy_sold_works_correctly():
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_WEEK,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        profile = {f"time_slot_{i}": 0.5 for i in range(3)}
        with patch.object(
                volume_time_series._trade_profile_generator,
                "generate_trade_profile", Mock(return_value=profile)) as profile_generator_mock:
            # profile generator should not be called when total_energy_bought is <= 0
            asset_stats = ForwardDeviceStats("UUID", DateTime(2020, 1, 1), DateTime(2020, 1, 1))
            volume_time_series._add_total_energy_sold(
                asset_stats, AvailableMarketTypes.YEAR_FORWARD)
            profile_generator_mock.assert_not_called()

            # profile generator should be called when total_energy_bought is > 0
            with patch.object(
                volume_time_series, "_add_to_volume_time_series"
            ) as add_to_volume_time_series_mock:
                asset_stats = ForwardDeviceStats(
                    "UUID", DateTime(2020, 1, 1), DateTime(2020, 1, 1), total_energy_sold=2,
                    total_earned_eur=0.6)
                volume_time_series._add_total_energy_sold(
                    asset_stats, AvailableMarketTypes.YEAR_FORWARD)
                profile_generator_mock.assert_called_once_with(
                    asset_stats.total_energy_sold, asset_stats.time_slot,
                    AvailableMarketTypes.YEAR_FORWARD
                )
                expected_calls = []
                for time_slot, energy in profile.items():
                    expected_calls.append(
                        call.do_work(
                            time_slot,
                            {
                                "energy_kWh": energy,
                                "trade_count": asset_stats.total_sell_trade_count,
                                "accumulated_trade_rates": asset_stats.accumulated_sell_trade_rates
                            },
                            AvailableMarketTypes.YEAR_FORWARD, "sold"
                        )
                    )
                assert add_to_volume_time_series_mock.call_count == 3
                add_to_volume_time_series_mock.assert_has_calls(expected_calls)

    @staticmethod
    def test_add_to_volume_time_series_works_correctly():
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_MONTH,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)
        time_slot = DateTime(2020, 1, 1)
        time_slot_info = {
            "energy_kWh": 1,
            "trade_count": 1,
            "accumulated_trade_rates": 0.3
        }
        volume_time_series._add_to_volume_time_series(
            time_slot, time_slot_info, AvailableMarketTypes.MONTH_FORWARD, "sold")
        sold_time_slot_data = volume_time_series.asset_time_series_buffer[time_slot.start_of(
            "year").year][str(time_slot)]["MONTH_FORWARD"]["sold"]
        assert sold_time_slot_data == {
            "energy_kWh": 1.0, "energy_rate": 0.3,
            "trade_count": 1, "accumulated_trade_rates": 0.3}

        time_slot_info = {
            "energy_kWh": 1,
            "trade_count": 2,
            "accumulated_trade_rates": 0.4
        }
        volume_time_series._add_to_volume_time_series(
            time_slot, time_slot_info, AvailableMarketTypes.MONTH_FORWARD, "sold")
        sold_time_slot_data = volume_time_series.asset_time_series_buffer[time_slot.start_of(
            "year").year][str(time_slot)]["MONTH_FORWARD"]["sold"]
        assert sold_time_slot_data == {
            "energy_kWh": 2.0, "energy_rate": 0.23,
            "trade_count": 3, "accumulated_trade_rates": 0.7}

    def test_add_asset_time_series_for_1_month_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 1-month resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_MONTH,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        try:
            for product_type, asset_stats in forward_time_series:
                volume_time_series.update_time_series(asset_stats, product_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)

    def test_add_asset_time_series_for_1_week_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 1-week resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_WEEK,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        try:
            for product_type, asset_stats in forward_time_series:
                volume_time_series.update_time_series(asset_stats, product_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)

    def test_add_asset_time_series_for_1_hour_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 1-hour resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_1_HOUR,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        try:
            for product_type, asset_stats in forward_time_series:
                volume_time_series.update_time_series(asset_stats, product_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)

    def test_add_asset_time_series_for_15_minutes_resolution(self, forward_time_series):
        """Call AssetVolumeTimeSeries in 15-minutes resolution to assure no KeyErrors happen."""
        volume_time_series = AssetVolumeTimeSeries(
            asset_uuid="UUID", asset_peak_kWh=5,
            resolution=AggregationResolution.RES_15_MINUTES,
            get_asset_volume_time_series_db=fake_get_asset_volume_time_series_db)

        try:
            for product_type, asset_stats in forward_time_series:
                volume_time_series.update_time_series(asset_stats, product_type)
        except KeyError as exc:
            pytest.fail(str(exc))

        self.check_time_slots_year(volume_time_series)
