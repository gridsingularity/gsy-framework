from typing import Union, Dict
from datetime import datetime

import requests
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.mappings import lookup_area, Area
from entsoe.parsers import parse_generation
from geopy.geocoders import Nominatim


ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"

GENERATION_PLANT_TO_CARBON_EMISSIONS = {
    # source: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7
    # keys match the generation plants in the entsoe API
    # values in gCO2eq/kWh
    "Fossil Gas": {"min": 410, "median": 490, "max": 650},
    "Wind Offshore": {"min": 8.0, "median": 12, "max": 35},
    "Hydro Pumped Storage": {"min": 1.0, "median": 24, "max": 2200},
    "Nuclear": {"min": 3.7, "median": 12, "max": 110},
    "Biomass": {"min": 620, "median": 740, "max": 890},
}


GEOPY_CONTRY_CODE_TO_ENTSOE_CODE = {
    "AL": "AL",
    "AD": "AD",
    "AT": "AT",
    "BY": "BY",
    "BE": "BE",
    "BA": "BA",
    "BG": "BG",
    "HR": "HR",
    "CY": "CY",
    "CZ": "CZ",
    "DK": "DK",
    "EE": "EE",
    "FI": "FI",
    "FR": "FR",
    "DE": "DE",
    "GR": "GR",
    "HU": "HU",
    "IS": "IS",
    "IE": "IE",
    "IT": "IT",
    "XK": "XK",
    "LV": "LV",
    "LI": "LI",
    "LT": "LT",
    "LU": "LU",
    "MT": "MT",
    "MD": "MD",
    "MC": "MC",
    "ME": "ME",
    "NL": "NL",
    "MK": "MK",
    "NO": "NO",
    "PL": "PL",
    "PT": "PT",
    "RO": "RO",
    "SM": "SM",
    "RS": "RS",
    "SK": "SK",
    "SI": "SI",
    "ES": "ES",
    "SE": "SE",
    "CH": "CH",
    "UA": "UA",
    "GB": "GB",
    "VA": "VA",
}

MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES = [
    "ES",
    "FI",
    "IT",
    "GR",
    "PA",
    "BR",
    "LT",
    "SK",
    "PE",
    "CA",
    "GB",
    "CY",
    "FR",
    "GB",
    "ID",
    "RO",
    "NZ",
    "CR",
    "HK",
    "IN",
    "SE",
    "PT",
    "LU",
    "JP",
    "BG",
    "CH",
    "HU",
    "NO",
    "IE",
    "LV",
    "CL",
    "HR",
    "ZA",
    "PH",
    "EE",
    "NL",
    "PL",
    "US",
    "TW",
    "DE",
    "SI",
    "AU",
    "TR",
    "BE",
    "NI",
    "DK",
    "AT",
    "SG",
    "IS",
    "KR",
    "BA",
    "UY",
    "IL",
    "CA",
    "RS",
    "CZ",
]


class EntsoePandasClientAdapter(EntsoePandasClient):
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key)

    def _base_request(
        self, params: Dict, start: pd.Timestamp, end: pd.Timestamp
    ) -> requests.Response:
        """Overwrites EntsoePandasClient _base_request method"""
        start_str = self._datetime_to_str(start)
        end_str = self._datetime_to_str(end)
        base_params = {
            "securityToken": self.api_key,
            "periodStart": start_str,
            "periodEnd": end_str,
        }
        params.update(base_params)
        response = self.session.get(url=ENTSOE_URL, params=params, proxies=None, timeout=None)
        return response

    def _query_generation_per_plant(
        self, country_code: Union[Area, str], start: pd.Timestamp, end: pd.Timestamp
    ):
        """Overwrites EntsoePandasClient query_generation_per_plant method"""
        print("start", start)
        print("end", end)
        area = lookup_area(country_code)
        params = {
            "documentType": "A73",
            "processType": "A16",
            "in_Domain": area.code,
        }
        response = self._base_request(params=params, start=start, end=end)
        text = response.text
        if "Unauthorized" in text:
            raise ValueError("Invalid API key")
        df_generation = parse_generation(text, per_plant=True, include_eic=False)
        print("df_generation", df_generation)
        df_generation.to_csv("df_generation.csv")
        if df_generation.empty:
            raise ValueError("The Entsoe dataframe is empty. Please check the query parameters.")
        df_generation.columns = df_generation.columns.set_levels(
            df_generation.columns.levels[0].str.encode("latin-1").str.decode("utf-8"), level=0
        )
        df_generation = df_generation.tz_convert(area.tz)
        # Truncation will fail if data is not sorted along the index in rare
        # cases. Ensure the dataframe is sorted:
        df_generation = df_generation.sort_index(axis=0)

        if df_generation.columns.nlevels == 2:
            df_generation = (
                df_generation.assign(newlevel="Actual Aggregated")
                .set_index("newlevel", append=True)
                .unstack("newlevel")
            )
        df_generation = df_generation.truncate(before=start, after=end)
        return df_generation


class CarbonEmissionsHandler:
    """The most recent Enstsoe-y version (v0.6.16) is only compatible with python 3.9.
    Therefore, I am using v0.4.4 whose URL does not work. So, I am overwriting some methods
    from https://github.com/EnergieID/entsoe-py (branch v0.4.4) to make this work.
    """

    def __init__(self, entsoe_api_key: str = None):
        self.entsoe_api_key = entsoe_api_key

    def coordinates_to_country_code(self, lat: float, lon: float) -> str:
        """Get the country code based on the coordinates"""
        geolocator = Nominatim(user_agent="location_app")
        location = geolocator.reverse((lat, lon), language="en")
        if location and "country" in location.raw["address"]:
            country_code = location.raw["address"]["country_code"].upper()
            return GEOPY_CONTRY_CODE_TO_ENTSOE_CODE[country_code]
        return "Country not found"

    def calculate_carbon_ratio(
        self, country_code: str, start: pd.Timestamp, end: pd.Timestamp, stat: str = "median"
    ) -> pd.DataFrame:
        """Calculate the total carbon generated based on the specified statistic
        (min, median, max)"""
        if stat not in ["min", "median", "max"]:
            raise ValueError("stat must be one of 'min', 'median', or 'max'")

        if (
            country_code in GEOPY_CONTRY_CODE_TO_ENTSOE_CODE.values()
        ):  # source: https://transparency.entsoe.eu/
            entsoe_client = EntsoePandasClientAdapter(api_key=self.entsoe_api_key)
            df_generation_per_plant = entsoe_client._query_generation_per_plant(
                country_code, start, end
            )
        elif (
            country_code in MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES
        ):  # source: https://www.electricitymaps.com/data-portal
            df_generation_per_plant = ...
        else:  # source: https://ourworldindata.org/
            df_generation_per_plant = ...

        generation_types = df_generation_per_plant.iloc[0].iloc[1:]
        print("stat", stat)
        # fmt: off
        carbon_emission_per_plant = lambda x: GENERATION_PLANT_TO_CARBON_EMISSIONS[  # noqa: E731
            x
        ][stat]
        # fmt: on
        print("carbon_emission_per_plant", carbon_emission_per_plant)
        print("generation_types", generation_types)
        emissions_map = generation_types.map(carbon_emission_per_plant)

        df_numeric = df_generation_per_plant.iloc[2:].reset_index(drop=True)
        df_numeric = df_numeric.set_index("Unnamed: 0").apply(  # noqa: E501
            pd.to_numeric, errors="coerce"
        )
        df_numeric.index = pd.to_datetime(df_numeric.index)
        df_numeric["Total Energy (kWh)"] = df_numeric.sum(axis=1) * 1000  # convert MWh to kWh
        df_numeric["Total Carbon (gCO2eq)"] = df_numeric.mul(emissions_map, axis=1).sum(axis=1)
        df_numeric["Ratio (gCO2eq/kWh)"] = (
            df_numeric["Total Carbon (gCO2eq)"] / df_numeric["Total Energy (kWh)"]
        )
        return df_numeric[["Ratio (gCO2eq/kWh)"]]

    def calculate_carbon_emissions_from_imported_energy(
        self, df_carbon_ratio: pd.DataFrame, df_imported_energy: pd.DataFrame
    ):
        """Calculate the carbon emissions based on the imported/exported energy"""

        df_carbon_ratio.index = pd.to_datetime(df_carbon_ratio.index)
        df_imported_energy["simulation_time"] = pd.to_datetime(
            df_imported_energy["simulation_time"]
        )
        df_combined = pd.merge(
            df_imported_energy,
            df_carbon_ratio,
            left_on="simulation_time",
            right_index=True,
            how="left",
        )
        df_combined["carbon_generated_base_case"] = (
            df_combined["imported_from_community"] + df_combined["imported_from_grid"]
        ) * df_combined["Ratio (gCO2eq/kWh)"]
        df_combined["carbon_generated_gsy"] = (
            df_combined["imported_from_grid"] * df_combined["Ratio (gCO2eq/kWh)"]
        )
        df_combined["carbon_savings"] = (
            df_combined["carbon_generated_base_case"] - df_combined["carbon_generated_gsy"]
        )
        df_combined = df_combined[
            [
                "simulation_time",
                "imported_from_community",
                "imported_from_grid",
                "carbon_generated_base_case",
                "carbon_generated_gsy",
                "carbon_savings",
            ]
        ]
        return df_combined

    def calculate_carbon_emissions_from_gsy_trade_profile(
        self, country_code: str, trade_profile: Dict
    ) -> Dict:
        """Calculate the carbon emissions based on the gsy-e trade profile
        (energy_bought, energy_sold)"""

        if "Grid" not in trade_profile:
            raise ValueError("Grid area not found")
        grid_area = trade_profile["Grid"]

        # Find simulation days
        for area in grid_area["sold_energy"].values():
            trades = list(area.values())[0]
            dates = sorted(
                set(pd.to_datetime(list(trades.keys()), format="%B %d %Y, %H:%M h").date)
            )
        start_date = pd.Timestamp(datetime.combine(dates[0], datetime.min.time())).round("H")
        end_date = pd.Timestamp(datetime.combine(dates[-1], datetime.max.time())).round("H")

        # calculate carbon ratio
        df_carbon_ratio = self.calculate_carbon_ratio(country_code, start_date, end_date)
        df_total_accumulated = pd.DataFrame()
        for area in grid_area["sold_energy"].values():
            # calculate carbon emissions
            accummulated = area["accumulated"]
            df_accumulated = pd.DataFrame(list(accummulated.items()), columns=["Time", "Value"])
            df_accumulated["Time"] = pd.to_datetime(
                df_accumulated["Time"], format="%B %d %Y, %H:%M h"
            )
            df_total_accumulated = (
                pd.concat([df_total_accumulated, df_accumulated])
                .groupby("Time", as_index=False)["Value"]
                .sum()
            )
        df_total_accumulated = df_total_accumulated.sort_values(by="Time").reset_index(drop=True)
        df_total_accumulated["Time"] = pd.to_datetime(
            df_total_accumulated["Time"], format="%B %d %Y, %H:%M h", utc=True
        )
        df_carbon_emissions = pd.merge(
            df_total_accumulated,
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
