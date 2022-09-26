from pendulum import DateTime, duration, period

from gsy_framework.forward_markets.aggregated_profile import (
    HourlyAggregatedSSPProfile, MonthlyAggregatedSSPProfile,
    QuarterHourAggregatedSSPProfile, WeeklyAggregatedSSPProfile,
    YearlyAggregatedSSPProfile)
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
    start_date = DateTime(2022, 8, 26, 6, 20)
    end_date = DateTime(2022, 9, 26, 8, 55)

    profile = list(aggregated_profile.generate(start_date, end_date))

    start_date = DateTime(2022, 8, 26, 6, 15)
    end_date = DateTime(2022, 9, 26, 8, 45)

    assert len(profile) == (end_date - start_date) / duration(minutes=15)
    assert profile[-1][0] == end_date - duration(minutes=15)
    assert profile[0][0] == start_date


def test_hourly_aggregated_ssp_profile_range():
    aggregated_profile = HourlyAggregatedSSPProfile(capacity_kWh=1)
    start_date = DateTime(2022, 9, 26, 7, 30)
    end_date = DateTime(2022, 9, 26, 22, 15)

    profile = list(aggregated_profile.generate(start_date, end_date))

    start_date = start_date.start_of("hour")
    end_date = end_date.start_of("hour")

    assert len(profile) == (end_date - start_date) / duration(hours=1)
    assert profile[-1][0] == end_date - duration(hours=1)
    assert profile[0][0] == start_date


def test_weekly_aggregated_ssp_profile_range():
    aggregated_profile = WeeklyAggregatedSSPProfile(capacity_kWh=1)
    start_date = DateTime(2021, 1, 1, 9, 0)
    end_date = DateTime(2021, 1, 16, 23, 0)

    profile = list(aggregated_profile.generate(start_date, end_date))

    start_date = start_date.start_of("week")
    end_date = end_date.start_of("week")

    assert len(profile) == (end_date - start_date) / duration(weeks=1)
    assert profile[-1][0] == end_date - duration(weeks=1)
    assert profile[0][0] == start_date


def test_monthly_aggregated_ssp_profile_range():
    aggregated_profile = MonthlyAggregatedSSPProfile(capacity_kWh=1)
    start_date = DateTime(2022, 3, 20, 9, 0)
    end_date = DateTime(2023, 4, 15, 23, 0)

    profile = list(aggregated_profile.generate(start_date, end_date))

    start_date = start_date.start_of("month")
    end_date = end_date.start_of("month")

    assert len(profile) == 13
    assert profile[-1][0] == end_date - duration(months=1)
    assert profile[0][0] == start_date


def test_yearly_aggregated_ssp_profile_range():
    aggregated_profile = YearlyAggregatedSSPProfile(capacity_kWh=1)
    start_date = DateTime(2020, 3, 20, 9, 0)
    end_date = DateTime(2025, 4, 15, 23, 0)

    profile = list(aggregated_profile.generate(start_date, end_date))

    start_date = start_date.start_of("year")
    end_date = end_date.start_of("year")

    assert len(profile) == 5
    assert profile[-1][0] == end_date - duration(years=1)
    assert profile[0][0] == start_date


def test_quarter_hour_aggregated_ssp_profile_values():
    aggregated_profile = QuarterHourAggregatedSSPProfile(capacity_kWh=2)
    start_date = DateTime(2022, 9, 26, 7, 15)
    end_date = DateTime(2022, 9, 27, 8, 45)

    profile = aggregated_profile.generate(start_date, end_date)

    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(minutes=15), 2)
        assert energy == expected_energy


def test_hourly_aggregated_ssp_profile_values():
    aggregated_profile = HourlyAggregatedSSPProfile(capacity_kWh=2)
    start_date = DateTime(2022, 9, 26, 7, 0)
    end_date = DateTime(2022, 9, 26, 22, 0)

    profile = aggregated_profile.generate(start_date, end_date)

    for time_slot, energy in profile:
        expected_energy = get_sum_of_ssp_profile_range_values(
            time_slot, time_slot + duration(hours=1), 2)
        assert energy == expected_energy
