from math import isclose

from pendulum import DateTime, duration, period

from gsy_framework.enums import AggregationResolution
from gsy_framework.forward_markets.aggregated_ssp_profile import (
    HourlyAggregatedSSPProfile, MonthlyAggregatedSSPProfile,
    QuarterHourAggregatedSSPProfile, WeeklyAggregatedSSPProfile,
    YearlyAggregatedSSPProfile, get_aggregated_SSP_profile)
from gsy_framework.forward_markets.forward_profile import (
    ProfileScaler, StandardProfileParser)


def get_sum_of_ssp_profile_range_values(
        start_time: DateTime, end_time: DateTime, capacity_kWh: float):
    """Return sum of scaled ssp generated energy from start_time to end_time."""
    result = 0
    profile = ProfileScaler(StandardProfileParser().parse()).scale_by_peak(peak_kWh=1)
    for time_slot in period(
            start_time, end_time - duration(minutes=15)).range("minutes", 15):
        result += profile[time_slot.month][time_slot.time()] * capacity_kWh
    return result


def test_quarter_hour_aggregated_ssp_profile_range():
    aggregated_profile = QuarterHourAggregatedSSPProfile(capacity_kWh=1)
    start_time = DateTime(2022, 8, 26, 6, 20)
    end_time = DateTime(2022, 9, 26, 8, 55)

    profile = list(aggregated_profile.generate(start_time, end_time))

    start_time = DateTime(2022, 8, 26, 6, 15)
    end_time = DateTime(2022, 9, 26, 8, 45)

    assert len(profile) == (end_time - start_time) / duration(minutes=15)
    assert profile[-1][0] == end_time - duration(minutes=15)
    assert profile[0][0] == start_time


def test_hourly_aggregated_ssp_profile_range():
    aggregated_profile = HourlyAggregatedSSPProfile(capacity_kWh=1)
    start_time = DateTime(2022, 9, 25, 7, 30)
    end_time = DateTime(2022, 9, 26, 22, 15)

    profile = list(aggregated_profile.generate(start_time, end_time))

    start_time = start_time.start_of("hour")
    end_time = end_time.start_of("hour")

    assert len(profile) == (end_time - start_time) / duration(hours=1)
    assert profile[-1][0] == end_time - duration(hours=1)
    assert profile[0][0] == start_time


def test_weekly_aggregated_ssp_profile_range():
    aggregated_profile = WeeklyAggregatedSSPProfile(capacity_kWh=1)
    start_time = DateTime(2021, 1, 1, 9, 0)
    end_time = DateTime(2021, 2, 16, 23, 0)

    profile = list(aggregated_profile.generate(start_time, end_time))

    start_time = start_time.start_of("week")
    end_time = end_time.start_of("week")

    assert len(profile) == (end_time - start_time) / duration(weeks=1)
    assert profile[-1][0] == end_time - duration(weeks=1)
    assert profile[0][0] == start_time


def test_monthly_aggregated_ssp_profile_range():
    aggregated_profile = MonthlyAggregatedSSPProfile(capacity_kWh=1)
    start_time = DateTime(2022, 2, 20, 9, 0)
    end_time = DateTime(2023, 4, 15, 23, 0)

    profile = list(aggregated_profile.generate(start_time, end_time))

    start_time = start_time.start_of("month")
    end_time = end_time.start_of("month")

    assert len(profile) == 14
    assert profile[-1][0] == end_time - duration(months=1)
    assert profile[0][0] == start_time


def test_yearly_aggregated_ssp_profile_range():
    aggregated_profile = YearlyAggregatedSSPProfile(capacity_kWh=1)
    start_time = DateTime(2020, 3, 20, 9, 0)
    end_time = DateTime(2025, 4, 15, 23, 0)

    profile = list(aggregated_profile.generate(start_time, end_time))

    start_time = start_time.start_of("year")
    end_time = end_time.start_of("year")

    assert len(profile) == 5
    assert profile[-1][0] == end_time - duration(years=1)
    assert profile[0][0] == start_time


def test_quarter_hour_aggregated_ssp_profile_values():
    profile = get_aggregated_SSP_profile(
        capacity_kWh=2,
        start_time=DateTime(2022, 9, 26, 7, 15),
        end_time=DateTime(2022, 9, 27, 8, 45),
        resolution=AggregationResolution.RES_15_MINUTES
    )
    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(minutes=15), 2)
        assert isclose(energy, expected_energy)


def test_hourly_aggregated_ssp_profile_values():
    profile = get_aggregated_SSP_profile(
        capacity_kWh=2,
        start_time=DateTime(2022, 8, 26, 7, 0),
        end_time=DateTime(2022, 9, 26, 22, 0),
        resolution=AggregationResolution.RES_1_HOUR
    )
    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(hours=1), 2)
        assert isclose(energy, expected_energy)


def test_weekly_aggregated_ssp_profile_values():
    profile = get_aggregated_SSP_profile(
        capacity_kWh=2,
        start_time=DateTime(2021, 1, 1, 9, 0),
        end_time=DateTime(2021, 2, 16, 23, 0),
        resolution=AggregationResolution.RES_1_WEEK
    )
    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(weeks=1), 2)
        assert isclose(energy, expected_energy)


def test_monthly_aggregated_ssp_profile_values():
    profile = get_aggregated_SSP_profile(
        capacity_kWh=2,
        start_time=DateTime(2021, 1, 1, 9, 0),
        end_time=DateTime(2021, 3, 16, 23, 0),
        resolution=AggregationResolution.RES_1_MONTH
    )
    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(months=1), 2)
        assert isclose(energy, expected_energy)


def test_yearly_aggregated_ssp_profile_values():
    profile = get_aggregated_SSP_profile(
        capacity_kWh=2,
        start_time=DateTime(2021, 1, 1, 9, 0),
        end_time=DateTime(2025, 3, 16, 23, 0),
        resolution=AggregationResolution.RES_1_YEAR
    )
    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(years=1), 2)
        assert isclose(energy, expected_energy)
