from typing import Union, Dict, List

import requests
import pandas as pd
from pendulum import duration
from entsoe import EntsoePandasClient
from entsoe.mappings import lookup_area, Area
from entsoe.parsers import parse_generation
from geopy.geocoders import Nominatim

from gsy_framework.sim_results.results_abc import ResultsBaseClass

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
    "BE": "BE",
    "PT": "PT",
    "ES": "ES",
    "FR": "FR",
    "DE": "DE",
    "NL": "NL",
    "IT": "IT",
    "SE": "SE",
    "NO": "NO",
    "FI": "FI",
    "DK": "DK",
    "AT": "AT",
    "CH": "CH",
    "GB": "GB",
    "IE": "IE",
    "PL": "PL",
    "CZ": "CZ",
    "SK": "SK",
    "HU": "HU",
    "SI": "SI",
    "HR": "HR",
    "RO": "RO",
    "BG": "BG",
    "GR": "GR",
    "EE": "EE",
    "LV": "LV",
    "LT": "LT",
    "LU": "LU",
    "MT": "MT",
    "CY": "CY",
}


class CarbonEmissionsHandler(EntsoePandasClient, ResultsBaseClass):
    """The most recent Enstsoe-y version (v0.6.16) is only compatible with python 3.9.
    Therefore, I am using v0.4.4 whose URL does not work. So, I am overwriting some methods
    from https://github.com/EnergieID/entsoe-py (branch v0.4.4) to make this work.
    """

    carbon_emissions = {}

    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key)

    def coordinates_to_country_code(self, lat: float, lon: float) -> str:
        """Get the country code based on the coordinates"""
        geolocator = Nominatim(user_agent="location_app")
        location = geolocator.reverse((lat, lon), language="en")
        if location and "country" in location.raw["address"]:
            country_code = location.raw["address"]["country_code"].upper()
            return GEOPY_CONTRY_CODE_TO_ENTSOE_CODE[country_code]
        return "Country not found"

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
        df = parse_generation(text, per_plant=True, include_eic=False)

        df.columns = df.columns.set_levels(
            df.columns.levels[0].str.encode("latin-1").str.decode("utf-8"), level=0
        )
        df = df.tz_convert(area.tz)
        # Truncation will fail if data is not sorted along the index in rare
        # cases. Ensure the dataframe is sorted:
        df = df.sort_index(axis=0)

        if df.columns.nlevels == 2:
            df = (
                df.assign(newlevel="Actual Aggregated")
                .set_index("newlevel", append=True)
                .unstack("newlevel")
            )
        df = df.truncate(before=start, after=end)
        return df

    def calculate_carbon_ratio(
        self, country_code: str, start: pd.Timestamp, end: pd.Timestamp, stat: str = "median"
    ) -> pd.DataFrame:
        """Calculate the total carbon generated based on the specified statistic
        (min, median, max)"""
        if stat not in ["min", "median", "max"]:
            raise ValueError("stat must be one of 'min', 'median', or 'max'")

        df = self._query_generation_per_plant(country_code, start, end)

        generation_types = df.iloc[0].iloc[1:]
        # fmt: off
        carbon_emission_per_plant = lambda x: GENERATION_PLANT_TO_CARBON_EMISSIONS[  # noqa: E731
            x
        ][stat]
        # fmt: on
        emissions_map = generation_types.map(carbon_emission_per_plant)

        df_numeric = df.iloc[2:].reset_index(drop=True)
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

    def update(self, country_code: str, time_slot: duration, results_list: List[Dict]):
        """Update the results_dict with carbon generated and carbon savings"""

        start_date = pd.Timestamp(results_list[0]["current_market"].split("T")[0])
        end_date = pd.Timestamp(results_list[-1]["current_market"].split("T")[0])
        df_carbon_ratio = self.calculate_carbon_ratio(country_code, start_date, end_date)
        df_carbon_ratio.to_csv("carbon_ratio.csv")
        for result in results_list:
            current_market = result["current_market"]

            for area_uuid in result["results"].keys():
                area_result = result["results"][area_uuid]
                target_timestamp = pd.Timestamp(current_market).tz_localize("UTC")

                # the closest timestamp to the target_timestamp
                nearest_index = df_carbon_ratio.index.get_indexer(
                    [target_timestamp], method="nearest"
                )[0]
                nearest_row = df_carbon_ratio.iloc[nearest_index]

                carbon_ratio = nearest_row["Ratio (gCO2eq/kWh)"]

                imported_energy_from_grid_kWh = area_result["bought_from_grid"]
                imported_energy_from_community_kWh = area_result[
                    "energy_bought_from_community_kWh"
                ]

                carbon_generated_base_case = (
                    imported_energy_from_grid_kWh + imported_energy_from_community_kWh
                ) * carbon_ratio
                carbon_generated_gsy = imported_energy_from_grid_kWh * carbon_ratio
                carbon_savings = carbon_generated_base_case - carbon_generated_gsy

                area_result["carbon_generated_g"] = carbon_generated_gsy
                area_result["carbon_savings_g"] = carbon_savings

        return results_list

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([self.carbon_emissions])

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        # pylint: disable=arguments-differ
        raise NotImplementedError("Merge not supported.")

    @property
    def raw_results(self):
        return self.carbon_emissions

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """No need for this as no state is needed"""
        pass
