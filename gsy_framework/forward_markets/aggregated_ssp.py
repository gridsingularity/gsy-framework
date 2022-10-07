import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable

from pendulum import DateTime, duration, period

from gsy_framework.enums import AggregationResolution
from gsy_framework.forward_markets.forward_profile import (
    ProfileScaler, StandardProfileParser, gsy_framework_path)

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
        assert end_time - start_time >= duration(minutes=15), \
            "Time period should be >= 15 minutes."
        return period(
            start=start_time.set(minute=(start_time.minute // 15) * 15),
            end=end_time.set(minute=(end_time.minute // 15) * 15) - duration(minutes=15)
        ).range("minutes", 15)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        return float(self._SSP_AGGREGATED_PROFILE[timeslot.month][timeslot.time()])

    def _load_aggregated_profiles(self) -> None:
        self._SSP_AGGREGATED_PROFILE = ProfileScaler(
            StandardProfileParser().parse()).scale_by_peak(peak_kWh=1)


class HourlyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return hourly-aggregated profile of the SSP."""
    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/hourly.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        assert end_time - start_time >= duration(hours=1), "Time period should be >= 1 hour."
        return period(
            start=start_time.start_of("hour"),
            end=end_time.start_of("hour") - duration(minutes=1)
        ).range("hours", 1)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        return float(self._SSP_AGGREGATED_PROFILE[timeslot.format("M-H")])


class WeeklyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return weekly-aggregated profile of the SSP."""

    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/daily.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        assert end_time - start_time >= duration(weeks=1), "Time period should be >= 1 week."
        return period(
            start_time.start_of("week"),
            end_time.start_of("week") - duration(weeks=1)
        ).range("weeks", 1)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        return sum([
            float(self._SSP_AGGREGATED_PROFILE[str(t.month)])
            for t in period(timeslot, timeslot.add(days=6)).range("days", 1)
        ])


class MonthlyAggregatedSSPProfile(AggregatedSSPProfileBase):
    """Return monthly-aggregated profile of the SSP."""
    SSP_AGGREGATED_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/non_leap_monthly.csv"
    LEAP_YEAR_SSP_AGGREGATED_PROFILE_PATH = RESOURCES_PATH / "aggregated_ssp/leap_monthly.csv"

    def _get_timeslots(self, start_time: DateTime, end_time: DateTime) -> Iterable:
        assert end_time - start_time >= duration(months=1), "Time period should be >= 1 month."
        return period(
            start=start_time.start_of("month"),
            end=end_time.start_of("month") - duration(days=1)
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
        assert end_time - start_time >= duration(years=1), "Time period should be >= 1 year."
        return period(
            start=start_time.start_of("year"),
            end=end_time.start_of("year") - duration(days=1),
        ).range("years", 1)

    def _get_timeslot_energy_kWh(self, timeslot: DateTime) -> float:
        if timeslot.is_leap_year():
            return float(self._LEAP_YEAR_SSP_AGGREGATED_PROFILE[""])
        return float(self._SSP_AGGREGATED_PROFILE[""])


def get_aggregated_SSP(
        capacity_kWh: float, start_time: DateTime,
        end_time: DateTime, resolution: AggregationResolution):
    """Return aggregated SSP profile with the specified resolution and with respect to
    start_time, end_time and asset capacity."""
    resolution_mapping = {
        AggregationResolution.RES_15_MINUTES: QuarterHourAggregatedSSPProfile,
        AggregationResolution.RES_1_HOUR: HourlyAggregatedSSPProfile,
        AggregationResolution.RES_1_WEEK: WeeklyAggregatedSSPProfile,
        AggregationResolution.RES_1_MONTH: MonthlyAggregatedSSPProfile,
        AggregationResolution.RES_1_YEAR: YearlyAggregatedSSPProfile
    }

    try:
        return resolution_mapping[resolution](capacity_kWh=capacity_kWh).generate(
            start_time=start_time, end_time=end_time
        )
    except KeyError as exc:
        raise ValueError(f"Unsupported resolution: {resolution}") from exc
