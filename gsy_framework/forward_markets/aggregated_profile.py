import csv
import itertools
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable

from pendulum import DateTime, Duration, duration, period

from gsy_framework.forward_markets.forward_profile import (
    StandardProfileParser, gsy_framework_path)

RESOURCES_PATH = Path(gsy_framework_path) / "resources"


class AggregatedSSPProfileBase(ABC):
    """Base class representing the Standard Solar Profile in different resolutions."""

    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH: Path = None
    LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH: Path = None

    def __init__(self, capacity_kWh: float):
        self.capacity_kWh = capacity_kWh

        self._SSP_AGGREGATED_PROFILE: Dict = {}
        self._LEAP_YEAR_SSP_AGGREGATED_PROFILE: Dict = {}

        self._load_aggregated_profiles()

    def generate(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        """Generate SSP profile with respect to start and end times in the correct resolution."""
        for timeslot in self._get_timeslots(start_time, end_time):
            yield timeslot, self._get_timeslot_energy_kWh(timeslot) * self.capacity_kWh

    def _load_aggregated_profiles(self) -> None:
        """Load aggregated SSP profiles from disk."""

        if self.SSP_AGGREGATED_AGGREGATED_PROFILE_PATH:
            with open(self.SSP_AGGREGATED_AGGREGATED_PROFILE_PATH, encoding="utf-8") as inf:
                reader = csv.DictReader(inf)
                for row in reader:
                    self._SSP_AGGREGATED_PROFILE[row["timeslot"]] = row["energy_kWh"]

        if self.LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH:
            with open(self.LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH, encoding="utf-8") as inf:
                reader = csv.DictReader(inf)
                for row in reader:
                    self._LEAP_YEAR_SSP_AGGREGATED_PROFILE[row["timeslot"]] = row["energy_kWh"]

    @abstractmethod
    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        """Return all timeslots with respect to start, end and resolution."""

    @abstractmethod
    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        """Return the energy amount associated with the timeslot."""


class QuarterHourAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return 15-minute-aggregated profile of the SSP."""
    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        return period(
            start=start_time.start_of("hour"),
            end=end_time.start_of("hour")
        ).range("minutes", 15)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        return float(self._SSP_AGGREGATED_PROFILE[timeslot.month][timeslot.time()])

    def _load_aggregated_profiles(self) -> None:
        self._SSP_AGGREGATED_PROFILE = StandardProfileParser().parse()


class HourlyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return hourly-aggregated profile of the SSP."""
    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/hourly.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        return period(
            start=start_time.start_of("hour"),
            end=end_time.start_of("hour")
        ).range("hours", 1)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        return float(self._SSP_AGGREGATED_PROFILE[timeslot.format("M-H")])


class WeeklyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return weekly-aggregated profile of the SSP."""

    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/non_leap_weekly.csv"
    LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/leap_weekly.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        start_day_week_no = (start_time.day_of_year // 7)
        start_time = start_time.start_of("year").add(weeks=start_day_week_no)
        periods = []
        for year in period(start_time.start_of("year"), end_time).range("years", 1):
            periods.append(
                period(
                    start=max(year, start_time),
                    end=min(year + duration(years=1), end_time)
                ).range("weeks", 1)
            )
        return itertools.chain(*periods)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        if timeslot.is_leap_year():
            return float(self._LEAP_YEAR_SSP_AGGREGATED_PROFILE[timeslot.format("M-D")])
        return float(self._SSP_AGGREGATED_PROFILE[timeslot.format("M-D")])


class MonthlyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return monthly-aggregated profile of the SSP."""
    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/non_leap_monthly.csv"
    LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/leap_monthly.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        return period(
            start=start_time.start_of("month"),
            end=end_time.start_of("month")
        ).range("months", 1)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        if timeslot.is_leap_year():
            return float(self._LEAP_YEAR_SSP_AGGREGATED_PROFILE[timeslot.format("M")])
        return float(self._SSP_AGGREGATED_PROFILE[timeslot.format("M")])


class YearlyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return yearly-aggregated profile of the SSP."""
    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/non_leap_yearly.csv"
    LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/leap_yearly.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        return period(
            start=start_time.start_of("year"),
            end=end_time.start_of("year")
        ).range("years", 1)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        if timeslot.is_leap_year():
            return float(self._LEAP_YEAR_SSP_AGGREGATED_PROFILE[""])
        return float(self._SSP_AGGREGATED_PROFILE[""])


def get_aggregated_SSP_profile(
        capacity_kWh: float, start_time: DateTime,
        end_time: DateTime, resolution: Duration
):
    """Return aggregated SSP profile with the specified resolution and with respect to
    start_time, end_time and device capacity."""
    resolution_mapping = {
        duration(minutes=15): QuarterHourAggregatedSSPProfile,
        duration(hours=1): HourlyAggregatedSSPProfile,
        duration(weeks=1): WeeklyAggregatedSSPProfile,
        duration(months=1): MonthlyAggregatedSSPProfile,
        duration(years=1): YearlyAggregatedSSPProfile
    }

    try:
        return resolution_mapping[resolution](capacity_kWh=capacity_kWh).generate(
            start_time=start_time, end_time=end_time
        )
    except KeyError as exc:
        raise ValueError(f"Unsupported resolution: {resolution}") from exc
