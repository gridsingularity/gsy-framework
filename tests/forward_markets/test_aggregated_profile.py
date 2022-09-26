from pendulum import DateTime, duration

from gsy_framework.forward_markets.aggregated_profile import (
    HourlyAggregatedSSPProfile, MonthlyAggregatedSSPProfile,
    QuarterHourAggregatedSSPProfile, WeeklyAggregatedSSPProfile,
    YearlyAggregatedSSPProfile)


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
