from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import csv

import pytz
from geopy.geocoders import Nominatim
from iso3166 import countries

from gsy_framework.constants_limits import DATE_TIME_FORMAT
from gsy_framework.sim_results.carbon_emissions.constants import (
    MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES,
)


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

    def _find_start_and_end_dates(
        self, dates: List, datetime_format: str = DATE_TIME_FORMAT
    ) -> Tuple[datetime, datetime]:
        """Find the start and end dates from a list of string timestamps"""

        dates = [datetime.strptime(timestr, datetime_format) for timestr in dates]
        start_date = min(dates).replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0)
        end_date = max(dates).replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0)
        return start_date, end_date

    def _full_range(self, start: datetime, end: datetime) -> List[datetime]:
        """Generate a list of datetime objects for each hour between start and end"""
        return [
            start + timedelta(hours=x)
            for x in range(int((end - start).total_seconds() // 3600) + 1)
        ]

    def query_carbon_ratio_from_static_source(
        self, country_code: str, start: datetime, end: datetime
    ) -> List[Dict]:
        """Calculate the total carbon generated based on the specified statistic"""

        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must have timezone")
        if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0):
            raise ValueError("start and end must be in UTC+0")

        if (
            country_code in MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES
        ):  # source: https://www.electricitymaps.com/data-portal

            file_path = (
                f"gsy_framework/resources/carbon_ratio_per_country/{country_code}_2023_monthly.csv"
            )
            data = {
                datetime.strptime(row["Datetime (UTC)"], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=pytz.UTC
                ): float(row["Carbon Intensity gCO₂eq/kWh (direct)"])
                for row in csv.DictReader(open(file_path, mode="r"))
            }

            full_range = self._full_range(start, end)
            carbon_ratio = [
                {
                    "time": time,
                    "Ratio (gCO2eq/kWh)": data.get(
                        time, data[max(k for k in data if k.month == time.month)]
                    ),
                    "country_code": country_code,
                }
                for time in full_range
            ]

        else:  # source: https://ourworldindata.org/grapher/carbon-intensity-electricity
            country_code_alpha3 = countries.get(country_code).alpha3
            file_path = (
                "gsy_framework/resources/carbon_ratio_per_country"
                "/carbon-intensity-electricity_yearly.csv"
            )

            # Find the carbon ratio for the most recent year
            with open(file_path, mode="r") as f:
                data = [
                    (int(row["Year"]), float(row["Carbon intensity of electricity - gCO2/kWh"]))
                    for row in csv.DictReader(f)
                    if row["Code"] == country_code_alpha3
                ]
            max_year = max(year for year, _ in data)
            carbon_ratio = next(value for year, value in data if year == max_year)

            # Assign carbon ratio values for each hour
            full_range = self._full_range(start, end)
            carbon_ratio = [
                {
                    "time": time,
                    "Ratio (gCO2eq/kWh)": carbon_ratio,
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

        if not all("Ratio (gCO2eq/kWh)" in obj for obj in carbon_ratio):
            raise ValueError("carbon_ratio must contain 'Ratio (gCO2eq/kWh)' in each entry")

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

        # Find the carbon ratio closest to the simulation time
        carbon_ratio_sorted = sorted(carbon_ratio, key=lambda x: x["time"])
        for obj in imported_energy:
            simluation_time = obj["simulation_time"]
            obj["carbon_ratio"] = min(
                carbon_ratio_sorted, key=lambda x: abs(x["time"] - simluation_time)
            )["Ratio (gCO2eq/kWh)"]

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
        usually from InfiniteBus accummulated sold_energy"""

        if len(trade_profile.keys()) == 0:
            raise ValueError("Invalid trade profile")

        # TODO: why trade_profile has "January 01 2024, 00:00 h" instead of "2024-01-01T00:00:00"
        start, end = self._find_start_and_end_dates(trade_profile.keys(), "%B %d %Y, %H:%M h")
        carbon_ratio = self.query_carbon_ratio_from_static_source(
            country_code=country_code,
            start=start,
            end=end,
        )

        carbon_generated_g = 0
        for time, value in trade_profile.items():
            time = datetime.strptime(time, "%B %d %Y, %H:%M h").replace(tzinfo=pytz.UTC)
            ratio = min(carbon_ratio, key=lambda x: abs(x["time"] - time))["Ratio (gCO2eq/kWh)"]
            if ratio is not None:
                carbon_generated_g += value * ratio
        carbon_emissions = {"carbon_generated_g": carbon_generated_g}

        return carbon_emissions

    def calculate_from_gsy_imported_exported_energy(
        self, country_code: str, imported_exported_energy: Dict
    ):
        """Calculate the carbon emissions from gsy-e imported exported energy
        which includes imported energy from community and grid."""

        first_key = next(iter(imported_exported_energy))
        area = imported_exported_energy[first_key]
        start_date, end_date = self._find_start_and_end_dates(area.keys(), "%Y-%m-%dT%H:%M:%S")

        carbon_ratio = self.query_carbon_ratio_from_static_source(
            country_code=country_code, start=start_date, end=end_date
        )

        imported_energy = [
            {
                "simulation_time": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").replace(
                    tzinfo=pytz.UTC
                ),
                "area_uuid": area_uuid,
                "imported_from_grid": data["imported_from_grid"],
                "imported_from_community": data["imported_from_community"],
            }
            for area_uuid, area in imported_exported_energy.items()
            for timestamp, data in area.items()
        ]

        print("imported_energy", imported_energy)
        print("carbon_ratio", carbon_ratio)
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
