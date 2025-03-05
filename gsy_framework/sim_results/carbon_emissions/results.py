from copy import deepcopy
from typing import Dict, List, Tuple
import csv
import logging

import pendulum
from pendulum import DateTime
from geopy.geocoders import Nominatim
from iso3166 import countries

from gsy_framework.constants_limits import TIME_ZONE
from gsy_framework.resources import STATIC_FILES_DIR
from gsy_framework.utils import str_to_pendulum_datetime
from gsy_framework.sim_results.carbon_emissions.constants import (
    MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES,
    CARBON_RATIO_G_KWH,
)

logger = logging.getLogger(__name__)


class CarbonEmissionsHandler:
    """The most recent Enstsoe-y version (v0.6.16) is only compatible with python 3.9.
    Therefore, I am using v0.4.4 whose URL does not work. So, I am overwriting some methods
    from https://github.com/EnergieID/entsoe-py (branch v0.4.4) to make this work.
    """

    def __init__(self):
        pass

    def coordinates_to_country_code(self, lat: float, lon: float) -> str:
        """Get the country code based on the coordinates"""
        geolocator = Nominatim(user_agent="location_app")
        location = geolocator.reverse((lat, lon), language="en")
        if location and "country" in location.raw["address"]:
            country_code = location.raw["address"]["country_code"].upper()
            return country_code
        return "Country not found"

    def _find_start_and_end_dates(self, dates: List) -> Tuple[DateTime, DateTime]:
        """Find the start and end dates from a list of string timestamps"""

        dates = [str_to_pendulum_datetime(timestr) for timestr in list(dates)]
        dates = [date.set(tz=TIME_ZONE) for date in dates]
        start_date = min(dates).start_of("hour").in_tz(TIME_ZONE)
        end_date = max(dates).start_of("hour").in_tz(TIME_ZONE)
        return start_date, end_date

    def _create_hourly_timestamps(self, start: DateTime, end: DateTime) -> List[DateTime]:
        """Generate a list of datetime objects for each hour between start and end"""
        return [start.add(hours=hour) for hour in range(int((end - start).total_hours()) + 1)]

    def query_carbon_ratio_from_static_source(
        self, country_code: str, start_time: DateTime, end_time: DateTime
    ) -> List[Dict]:
        """Calculate the total carbon generated based on the specified statistic"""

        if start_time.tzinfo is None or end_time.tzinfo is None:
            raise ValueError("start and end must have timezone")
        if start_time.tzname() != TIME_ZONE or end_time.tzname() != TIME_ZONE:
            raise ValueError("start and end must be in UTC+0")

        if (
            country_code in MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES
        ):  # source: https://www.electricitymaps.com/data-portal
            file_path = (
                f"{STATIC_FILES_DIR}/carbon_ratio_per_country/{country_code}_2023_monthly.csv"
            )

            with open(file_path, mode="r", encoding="utf-8") as carbon_file:
                data = {
                    pendulum.parse(row["Datetime (UTC)"], tz=TIME_ZONE): float(
                        row["Carbon Intensity gCO₂eq/kWh (direct)"]
                    )
                    for row in csv.DictReader(carbon_file)
                }

            full_range = self._create_hourly_timestamps(start_time, end_time)
            carbon_ratio = [
                {
                    "time": time,
                    CARBON_RATIO_G_KWH: data.get(
                        time, data.get(pendulum.datetime(2023, time.month, 1, tz=TIME_ZONE))
                    ),
                    "country_code": country_code,
                }
                for time in full_range
            ]

        else:  # source: https://ourworldindata.org/grapher/carbon-intensity-electricity
            country_code_alpha3 = countries.get(country_code).alpha3
            file_path = (
                f"{STATIC_FILES_DIR}/carbon_ratio_per_country"
                "/carbon-intensity-electricity_yearly.csv"
            )

            # Find the carbon ratio for the most recent year
            with open(file_path, mode="r", encoding="utf-8") as f:
                data = {
                    int(row["Year"]): float(row["Carbon intensity of electricity - gCO2/kWh"])
                    for row in csv.DictReader(f)
                    if row["Code"] == country_code_alpha3
                }
            max_year = max(data.keys())
            carbon_ratio = next(value for year, value in data.items() if year == max_year)

            # Assign carbon ratio values for each hour
            full_range = self._create_hourly_timestamps(start_time, end_time)
            carbon_ratio = [
                {
                    "time": time,
                    CARBON_RATIO_G_KWH: carbon_ratio,
                    "country_code": country_code,
                }
                for time in full_range
            ]

        return carbon_ratio

    def calculate_from_carbon_ratio_and_imported_energy(
        self, carbon_ratio: Dict, imported_energy: Dict
    ):
        """Calculate the carbon emissions from a dict with carbon ratios
        and another with imported/exported energy."""

        if not all({CARBON_RATIO_G_KWH, "time"}.issubset(obj) for obj in carbon_ratio):
            raise ValueError(
                "Each entry in carbon_ratio must contain keys: ", f"{CARBON_RATIO_G_KWH}, time"
            )

        if not all(
            {
                "simulation_time",
                "area_uuid",
                "imported_from_grid",
                "imported_from_community",
            }.issubset(obj)
            for obj in imported_energy
        ):
            raise ValueError(
                "Each entry in imported_energy must contain keys: ",
                "simulation_time, area_uuid, imported_from_grid, imported_from_community",
            )

        carbon_ratio_dict = {
            carbon_obj["time"]: carbon_obj[CARBON_RATIO_G_KWH] for carbon_obj in carbon_ratio
        }
        for obj in imported_energy:
            try:
                obj["carbon_ratio"] = carbon_ratio_dict[obj["simulation_time"]]
            except KeyError:
                # No carbon footprint data from this timestamp, trying the data from the start of
                # the hour at the same date.
                query_time: DateTime = deepcopy(obj["simulation_time"])
                query_time = query_time.set(minute=0, second=0)
                try:
                    obj["carbon_ratio"] = carbon_ratio_dict[query_time]
                except KeyError:
                    logger.info(
                        "Carbon footprint data not available for time %s. Setting 0.",
                        obj["simulation_time"],
                    )
                    obj["carbon_ratio"] = 0.0

        # Calculate carbon emissions
        for obj in imported_energy:
            obj["carbon_generated_base_case_g"] = (
                obj["imported_from_community"] + obj["imported_from_grid"]
            ) * obj["carbon_ratio"]

            obj["carbon_generated_gsy_g"] = obj["imported_from_grid"] * obj["carbon_ratio"]

            obj["carbon_savings_g"] = (
                obj["carbon_generated_base_case_g"] - obj["carbon_generated_gsy_g"]
            )

        return imported_energy

    def calculate_from_gsy_trade_profile(self, country_code: str, trade_profile: Dict) -> Dict:
        """Calculate the carbon emissions from gsy-e trade profile,
        usually from InfiniteBus accumulated sold_energy"""

        if len(trade_profile.keys()) == 0:
            raise ValueError("Invalid trade profile")

        start, end = self._find_start_and_end_dates(trade_profile.keys())
        carbon_ratio = self.query_carbon_ratio_from_static_source(
            country_code=country_code,
            start_time=start,
            end_time=end,
        )

        carbon_generated_g = 0
        for time, value in trade_profile.items():
            time = str_to_pendulum_datetime(time)
            ratio = min(carbon_ratio, key=lambda x, req_time=time: abs(x["time"] - req_time))[
                CARBON_RATIO_G_KWH
            ]
            if ratio is not None:
                carbon_generated_g += value * ratio
        carbon_emissions = {"carbon_generated_g": carbon_generated_g}

        return carbon_emissions

    def calculate_from_gsy_imported_exported_energy_with_carbon_ratio(
        self, carbon_ratio: List, imported_exported_energy: Dict
    ):
        """Calculate the carbon emissions from gsy-e imported exported energy
        which includes imported energy from community and grid."""
        imported_energy = [
            {
                "simulation_time": pendulum.parse(timestamp, tz=TIME_ZONE),
                "area_uuid": area_uuid,
                "imported_from_grid": data["imported_from_grid"],
                "imported_from_community": data["imported_from_community"],
            }
            for area_uuid, area in imported_exported_energy.items()
            for timestamp, data in area.items()
        ]
        carbon_emissions = self.calculate_from_carbon_ratio_and_imported_energy(
            carbon_ratio, imported_energy
        )
        total_emissions = {
            key: sum(obj[key] for obj in carbon_emissions)
            for key in [
                "carbon_generated_base_case_g",
                "carbon_generated_gsy_g",
                "carbon_savings_g",
            ]
        }
        return total_emissions
