from typing import Dict, List, Tuple
from datetime import datetime

import pytz

import pandas as pd
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

    def calculate_carbon_ratio(
        self, country_code: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        """Calculate the total carbon generated based on the specified statistic"""

        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must have timezone")
        if start.utcoffset() != pd.Timedelta(0) or end.utcoffset() != pd.Timedelta(0):
            raise ValueError("start and end must be in UTC+0")

        if (
            country_code in MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES
        ):  # source: https://www.electricitymaps.com/data-portal
            file_path = (
                f"gsy_framework/resources/carbon_ratio_per_country/{country_code}_2023_monthly.csv"
            )
            df_file = pd.read_csv(file_path, index_col=0, parse_dates=True).tz_localize("UTC")
            full_range = pd.date_range(start=start, end=end, freq="H", tz="UTC")
            df_carbon_ratio = df_file[["Carbon Intensity gCO₂eq/kWh (direct)"]].reindex(
                full_range, method="ffill"
            )
            df_carbon_ratio.rename(
                columns={"Carbon Intensity gCO₂eq/kWh (direct)": "Ratio (gCO2eq/kWh)"},
                inplace=True,
            )
        else:  # source: https://ourworldindata.org/grapher/carbon-intensity-electricity
            country_code_alpha3 = countries.get(country_code).alpha3
            file_path = (
                "gsy_framework/resources/carbon_ratio_per_country"
                "/carbon-intensity-electricity_yearly.csv"
            )
            df_file = pd.read_csv(file_path, index_col=2)
            df_file = df_file[df_file["Code"] == country_code_alpha3]

            df_file = df_file.loc[df_file.index.get_level_values(0).max()]  # filter fix max year
            full_range = pd.date_range(start=start, end=end, freq="H", tz="UTC")
            df_carbon_ratio = pd.DataFrame(index=full_range)
            df_carbon_ratio["Ratio (gCO2eq/kWh)"] = df_file[
                "Carbon intensity of electricity - gCO2/kWh"
            ]

        # fill df_carbon_ratio in case of missing hours using the last value
        df_carbon_ratio = df_carbon_ratio[["Ratio (gCO2eq/kWh)"]]
        df_carbon_ratio = df_carbon_ratio.reindex(
            pd.date_range(start=start, end=end, freq="H", tz="UTC"), method="pad"
        )
        return df_carbon_ratio

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
        start_date, end_date = self._find_start_and_end_dates(
            trade_profile.keys(), "%B %d %Y, %H:%M h"
        )

        # calculate carbon ratio
        df_carbon_ratio = self.calculate_carbon_ratio(
            country_code=country_code,
            start=pd.Timestamp(start_date),
            end=pd.Timestamp(end_date),
        )

        df_accumulated = pd.DataFrame(list(trade_profile.items()), columns=["Time", "Value"])
        df_accumulated = df_accumulated.sort_values(by="Time").reset_index(drop=True)
        df_accumulated["Time"] = pd.to_datetime(
            df_accumulated["Time"], format="%B %d %Y, %H:%M h", utc=True
        )
        df_carbon_emissions = pd.merge(
            df_accumulated,
            df_carbon_ratio,
            left_on="Time",
            right_index=True,
            how="inner",
        )
        df_carbon_emissions["Carbon Generated (gCO2eq)"] = (
            df_carbon_emissions["Value"] * df_carbon_emissions["Ratio (gCO2eq/kWh)"]
        )
        carbon_generated_g = df_carbon_emissions["Carbon Generated (gCO2eq)"].sum()

        emissions = {"carbon_generated_g": carbon_generated_g}
        return emissions

    def calculate_from_gsy_imported_exported_energy(
        self, country_code: str, imported_exported_energy: Dict
    ):
        """Calculate the carbon emissions from gsy-e imported exported energy
        which includes imported energy from community and grid."""

        first_key = next(iter(imported_exported_energy))
        area = imported_exported_energy[first_key]
        start_date, end_date = self._find_start_and_end_dates(area.keys(), "%Y-%m-%dT%H:%M:%S")

        df_carbon_ratio = self.calculate_carbon_ratio(
            country_code=country_code, start=pd.Timestamp(start_date), end=pd.Timestamp(end_date)
        )

        # populate df_total_accumualted with child areas imported energy
        df_total_accumulated = pd.DataFrame(
            columns=[
                "simulation_time",
                "area_uuid",
                "imported_from_grid",
                "imported_from_community",
            ]
        )
        for area_uuid, area in imported_exported_energy.items():
            for timestamp, imported_energy in area.items():
                df_imported_energy = pd.DataFrame(
                    {
                        "simulation_time": pd.to_datetime(timestamp).tz_localize("UTC"),
                        "area_uuid": area_uuid,
                        "imported_from_grid": imported_energy["imported_from_grid"],
                        "imported_from_community": imported_energy["imported_from_community"],
                    },
                    index=[0],
                )
                df_total_accumulated = (
                    pd.concat([df_total_accumulated, df_imported_energy])
                    .groupby(["simulation_time", "area_uuid"], as_index=False)
                    .sum()
                )

        df_carbon_emissions = self.calculate_from_carbon_ratio_and_imported_energy(
            df_carbon_ratio, df_total_accumulated
        )
        total_emissions = df_carbon_emissions.drop(columns=["simulation_time"]).sum().to_dict()
        return total_emissions
