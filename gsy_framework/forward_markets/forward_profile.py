import csv
import inspect
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict

import pendulum

import gsy_framework
from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.forward_markets.utils import create_market_slots

gsy_framework_path = os.path.dirname(inspect.getsourcefile(gsy_framework))


# The Standard Solar Profile energy parameters in this module are not used for Intraday Markets
ALLOWED_MARKET_TYPES = [
    AvailableMarketTypes.DAY_FORWARD,
    AvailableMarketTypes.WEEK_FORWARD,
    AvailableMarketTypes.MONTH_FORWARD,
    AvailableMarketTypes.YEAR_FORWARD,
]


class StandardProfileException(Exception):
    """Exception for the StandardProfile."""


class StandardProfileParser:
    """Class representing the Standard Solar Profile for forward products."""

    FILENAME = Path(gsy_framework_path) / "resources/standard_solar_profile.csv"
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    FIELDNAMES = ["INTERVAL"] + MONTHS
    SLOT_LENGTH = pendulum.duration(minutes=15)
    SLOTS_IN_ONE_HOUR = pendulum.duration(hours=1) / SLOT_LENGTH

    @classmethod
    def parse(cls) -> Dict:
        """Parse the standard solar profile.

        Returns: a dict where the keys are the numbers of the months and the values are dicts of
            {time: value} items.
        """
        data = defaultdict(dict)
        with open(cls.FILENAME, "r", encoding="utf-8") as inf:
            reader = csv.DictReader(inf, fieldnames=cls.FIELDNAMES, delimiter=";")
            next(reader)  # Skip header line
            for row in reader:
                # Only keep time, discarding the date information to make the profile more general
                slot = pendulum.parse(row["INTERVAL"], exact=True)
                # The SSP is expressed in power (kW) units, so we convert it to energy (kWh)
                for month_idx, month in cls._enumerate_months():
                    data[month_idx][slot] = float(row[month]) / cls.SLOTS_IN_ONE_HOUR

        return dict(data)

    @classmethod
    def _enumerate_months(cls):
        return enumerate(cls.MONTHS, start=1)


class ForwardTradeProfileGenerator:
    """
    Class to generate a new profile that spreads the trade energy across multiple market slots.

    The values of this profile are obtained by scaling the values of the Standard Solar Profile.
    """

    _STANDARD_SOLAR_PROFILE = StandardProfileParser.parse()

    def __init__(self, peak_kWh: float):
        self._scaler = ProfileScaler(self._STANDARD_SOLAR_PROFILE)
        self._scaled_capacity_profile = self._scaler.scale_by_peak(peak_kWh=peak_kWh)

    def generate_trade_profile(
        self, energy_kWh: float, market_slot: pendulum.DateTime, product_type: AvailableMarketTypes
    ):
        """Generate a profile based on the market slot and the product type."""
        assert energy_kWh > 0, f"The traded energy must be positive. energy_kWh: {energy_kWh}"

        if product_type == AvailableMarketTypes.INTRADAY:
            return {market_slot: energy_kWh}

        trade_profile = self._scaler.scale_by_peak(peak_kWh=energy_kWh)

        # This subtraction is done _before_ expanding the slots to improve performance
        # residual_energy_profile = self._subtract_profiles(
        #     self._scaled_capacity_profile, trade_profile)

        # Target a specific market slot based on the product type and market_slot.
        return self._expand_profile_slots(trade_profile, market_slot, product_type)

    @staticmethod
    def _expand_profile_slots(
        profile: Dict[int, Dict[pendulum.Time, float]],
        market_slot: pendulum.DateTime,
        product_type: AvailableMarketTypes,
    ):
        """
        Create all the profile slots targeting a specific period of time.

        The period depends on the type of the product (e.g. yearly/monthly/etc.).

        Return:
            A new profile complete with all time slots. E.g.:
                {
                    <time_slot>: value,
                    ...
                }
        """
        assert product_type in ALLOWED_MARKET_TYPES

        period_string_mapping = {
            AvailableMarketTypes.YEAR_FORWARD: "year",
            AvailableMarketTypes.MONTH_FORWARD: "month",
            AvailableMarketTypes.WEEK_FORWARD: "week",
            AvailableMarketTypes.DAY_FORWARD: "day",
        }

        time_slots = create_market_slots(
            start_time=market_slot.start_of(period_string_mapping[product_type]),
            end_time=market_slot.end_of(period_string_mapping[product_type]),
            slot_length=pendulum.duration(minutes=15),
        )
        assert time_slots
        new_profile = {}
        # Create all 15-minutes slots required by the product
        for slot in time_slots:
            try:
                new_profile[slot] = profile[slot.month][slot.time()]
            except KeyError as ex:
                raise StandardProfileException(
                    "There is no slot in the Standard Profile for the requested time. "
                    f"Month: {slot.month}, time: {slot.time()}"
                ) from ex

        return new_profile

    @staticmethod
    def _subtract_profiles(
        profile_A: Dict[int, Dict[pendulum.Time, float]],
        profile_B: Dict[int, Dict[pendulum.Time, float]],
    ):
        """Subtract the values in the profile dictionaries.

        Each dictionary has the following structure:
            {
                <month_number>: {<time_slot>: <value>, ...}
                ...
            }
        where `month_number` is just the index of the month in the year (starting from 1).
        """
        assert profile_A.keys() == profile_B.keys()

        return {
            month_number: {
                date: profile_A[month_number][date] - profile_B[month_number][date]
                for date in profile_A[month_number]
            }
            for month_number in profile_A
        }


class ProfileScaler:
    """Class to scale existing profiles based on a new peak.

    NOTE: the profile values must represent energy (kWh).
    """

    def __init__(self, profile: Dict):
        self._original_profile: Dict[int, Dict[pendulum.DateTime, float]] = profile
        self._original_peak_kWh: float = self._compute_original_peak_kWh()

    def scale_by_peak(self, peak_kWh: float) -> Dict[int, Dict[pendulum.Time, float]]:
        """Return a profile obtained by scaling the original one using a new peak capacity."""
        scaling_factor = self._compute_scaling_factor(peak_kWh)
        return self._scale_by_factor(scaling_factor)

    def _compute_original_peak_kWh(self) -> float:
        return max(
            energy_kWh
            for representative_day in self._original_profile.values()
            for energy_kWh in representative_day.values()
        )

    def _compute_scaling_factor(self, peak_kWh: float) -> float:
        """Compute the ratio to be used to scale the original profile based on the new peak."""
        return peak_kWh / self._original_peak_kWh

    def _scale_by_factor(self, scaling_factor: float):
        """Scale the original profile using the scaling factor."""
        scaled_profile = {}
        for month_idx, representative_day in self._original_profile.items():
            scaled_profile[month_idx] = {
                time: energy_kWh * scaling_factor
                for time, energy_kWh in representative_day.items()
            }

        return scaled_profile
