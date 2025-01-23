from typing import Union, Dict
from datetime import datetime
from enum import Enum

import requests
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.mappings import lookup_area, Area
from entsoe.parsers import parse_generation
from geopy.geocoders import Nominatim


ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"


class Stat(Enum):
    MIN = "min"
    MEDIAN = "median"
    MAX = "max"


GENERATION_PLANT_TO_CARBON_EMISSIONS = {
    # source: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7
    # keys match the generation plants in the entsoe API
    # values in gCO2eq/kWh
    "Solar": {Stat.MIN: 18, Stat.MEDIAN: 48, Stat.MAX: 180},
    "Wind Onshore": {Stat.MIN: 7.0, Stat.MEDIAN: 11, Stat.MAX: 56},
    "Fossil Gas": {Stat.MIN: 410, Stat.MEDIAN: 490, Stat.MAX: 650},
    "Wind Offshore": {Stat.MIN: 8.0, Stat.MEDIAN: 12, Stat.MAX: 35},
    "Hydro Pumped Storage": {Stat.MIN: 1.0, Stat.MEDIAN: 24, Stat.MAX: 2200},
    "Nuclear": {Stat.MIN: 3.7, Stat.MEDIAN: 12, Stat.MAX: 110},
    "Biomass": {Stat.MIN: 620, Stat.MEDIAN: 740, Stat.MAX: 890},
    "Hydro Water Reservoir": {
        Stat.MIN: 1.0,
        Stat.MEDIAN: 24,
        Stat.MAX: 2200,
    },  # same as Hydro Pumped
    "Fossil Oil": {Stat.MIN: 410, Stat.MEDIAN: 490, Stat.MAX: 650},  # same as Fossil Gas
    "Hydro Run-of-river and poundage": {
        Stat.MIN: 1.0,
        Stat.MEDIAN: 24,
        Stat.MAX: 2200,
    },  # (same as Hydro Pumped),
    "Fossil Hard coal": {Stat.MIN: 740, Stat.MEDIAN: 820, Stat.MAX: 910},
    "Fossil Coal-derived gas": {
        Stat.MIN: 740,
        Stat.MEDIAN: 820,
        Stat.MAX: 910,
    },  # same as Fossil Gas
    "Fossil Brown coal/Lignite": {
        Stat.MIN: 740,
        Stat.MEDIAN: 820,
        Stat.MAX: 910,
    },  # same as Fossil Hard coal
    "Other": {Stat.MIN: 50, Stat.MEDIAN: 300, Stat.MAX: 600},  # estimation
}


GEOPY_TO_ENTSOE_COUNTRY_CODE = (
    {  # see mappings https://github.com/EnergieID/entsoe-py/blob/master/entsoe/mappings.py
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
        "DE": "DE_AMPRION",
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
)

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

        # check if empty
        if df_generation.empty:
            raise ValueError("The Entsoe dataframe is empty. Please check the query parameters.")
        # localize or covert to UTC+0
        if df_generation.index.tzinfo is not None:
            df_generation.index = df_generation.index.tz_convert("UTC")
        else:
            df_generation.index = df_generation.index.tz_localize("UTC")

        # df_generation is a MultiIndex DataFrame
        df_generation.columns = df_generation.columns.set_levels(
            df_generation.columns.levels[0].str.encode("latin-1").str.decode("utf-8"), level=0
        )
        # Truncation will fail if data is not sorted along the index
        df_generation = df_generation.sort_index(axis=0)
        if df_generation.columns.nlevels == 2:
            df_generation = (
                df_generation.assign(newlevel="Actual Aggregated")
                .set_index("newlevel", append=True)
                .unstack("newlevel")
            )
        df_generation = df_generation.loc[start:end]

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
            return country_code
        return "Country not found"

    def _query_from_entsoe(
        self, country_code: str, start: pd.Timestamp, end: pd.Timestamp, stat: Stat = Stat.MEDIAN
    ):
        """Query generation per plant from the Entsoe API"""
        entsoe_client = EntsoePandasClientAdapter(api_key=self.entsoe_api_key)
        country_code = GEOPY_TO_ENTSOE_COUNTRY_CODE[country_code]
        df_generation_per_plant = entsoe_client._query_generation_per_plant(
            country_code, start, end
        )

        # df_generation_per_plant is a MultiIndex DataFrame
        generation_types = df_generation_per_plant.columns.get_level_values(1)
        emissions_map = pd.Series(
            [
                GENERATION_PLANT_TO_CARBON_EMISSIONS[generation_type][stat]
                for generation_type in generation_types
            ],
            index=df_generation_per_plant.columns,  # Map emissions to columns
        )

        df_numeric = df_generation_per_plant.iloc[0:].apply(pd.to_numeric, errors="coerce")

        df_numeric.index = pd.to_datetime(df_numeric.index, utc=True)
        df_numeric["Total Energy (kWh)"] = df_numeric.sum(axis=1) * 1000  # convert MWh to kWh
        df_numeric["Total Carbon (gCO2eq)"] = df_numeric.mul(emissions_map, axis=1).sum(axis=1)
        df_numeric["Ratio (gCO2eq/kWh)"] = (
            df_numeric["Total Carbon (gCO2eq)"] / df_numeric["Total Energy (kWh)"]
        )

        # format columns to be only one level
        df_numeric.columns = ["_".join(filter(None, map(str, col))) for col in df_numeric.columns]

        return df_numeric

    def calculate_carbon_ratio(
        self, country_code: str, start: pd.Timestamp, end: pd.Timestamp, stat: Stat = Stat.MEDIAN
    ) -> pd.DataFrame:
        """Calculate the total carbon generated based on the specified statistic
        (min, median, max)"""
        if stat not in [Stat.MIN, Stat.MEDIAN, Stat.MAX]:
            raise ValueError("stat must be one of 'min', 'median', or 'max'")
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must have timezone")
        if start.utcoffset() != pd.Timedelta(0) or end.utcoffset() != pd.Timedelta(0):
            raise ValueError("start and end must be in UTC+0")

        if (
            country_code in GEOPY_TO_ENTSOE_COUNTRY_CODE.keys()
        ):  # source: https://transparency.entsoe.eu/
            df_carbon_ratio = self._query_from_entsoe(country_code, start, end, stat)
        elif (
            country_code in MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES
        ):  # source: https://www.electricitymaps.com/data-portal
            df_carbon_ratio = ...
        else:  # source: https://ourworldindata.org/grapher/carbon-intensity-electricity
            df_carbon_ratio = ...

        # fill df_carbon_ratio in case of missing hours using the last value
        df_carbon_ratio = df_carbon_ratio[["Ratio (gCO2eq/kWh)"]]
        df_carbon_ratio = df_carbon_ratio.reindex(
            pd.date_range(start=start, end=end, freq="H", tz="UTC"), method="pad"
        )
        return df_carbon_ratio

    def calculate_from_carbon_ratio_and_imported_energy(
        self, df_carbon_ratio: pd.DataFrame, df_imported_energy: pd.DataFrame
    ):
        """Calculate the carbon emissions from a dataframe with carbon ratios
        and another with imported/exported energy."""

        if not {"Ratio (gCO2eq/kWh)"}.issubset(df_carbon_ratio.columns):
            raise ValueError(
                "df_carbon_ratio must contain columns: simulation_time, Ratio (gCO2eq/kWh)"
            )
        if not {
            "simulation_time",
            "area_uuid",
            "imported_from_grid",
            "imported_from_community",
        }.issubset(df_imported_energy.columns):
            raise ValueError(
                "df_imported_energy must contain columns: simulation_time, \
                imported_from_grid, imported_from_community"
            )

        df_carbon_ratio.index = pd.to_datetime(df_carbon_ratio.index)
        df_imported_energy["simulation_time"] = pd.to_datetime(
            df_imported_energy["simulation_time"], utc=True
        )

        # Find the nearest ratio for each df_imported_energy timestamp
        df_imported_energy["carbon_ratio"] = df_imported_energy["simulation_time"].apply(
            lambda ts: df_carbon_ratio.iloc[
                df_carbon_ratio.index.get_indexer([ts], method="nearest")[0]
            ]
        )
        df_imported_energy["carbon_generated_base_case_g"] = (
            df_imported_energy["imported_from_community"]
            + df_imported_energy["imported_from_grid"]
        ) * df_imported_energy["carbon_ratio"]

        df_imported_energy["carbon_generated_gsy_g"] = (
            df_imported_energy["imported_from_grid"] * df_imported_energy["carbon_ratio"]
        )

        df_imported_energy["carbon_savings_g"] = (
            df_imported_energy["carbon_generated_base_case_g"]
            - df_imported_energy["carbon_generated_gsy_g"]
        )
        return df_imported_energy

    def calculate_from_gsy_trade_profile(self, country_code: str, trade_profile: Dict) -> Dict:
        """Calculate the carbon emissions from gsy-e trade profile,
        usually from InfiniteBus accummulated sold_energy"""

        if len(trade_profile.keys()) == 0:
            raise ValueError("Invalid trade profile")

        # Find start and end dates
        dates = sorted(
            set(pd.to_datetime(list(trade_profile.keys()), format="%B %d %Y, %H:%M h").date)
        )
        start_date = pd.Timestamp(datetime.combine(dates[0], datetime.min.time())).round("H")
        end_date = pd.Timestamp(datetime.combine(dates[-1], datetime.max.time())).round("H")

        # calculate carbon ratio
        df_carbon_ratio = self.calculate_carbon_ratio(country_code, start_date, end_date)

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

        # Find simulation start and end dates
        area = imported_exported_energy[0]
        area.pop("accumulated")
        dates_keys = list(area.keys())
        dates = sorted(set(pd.to_datetime(list(dates_keys), format="%Y-%m-%dT%H:%M:%S").date))
        start_date = pd.Timestamp(datetime.combine(dates[0], datetime.min.time())).round("H")
        end_date = pd.Timestamp(datetime.combine(dates[-1], datetime.max.time())).round("H")

        df_carbon_ratio = self.calculate_carbon_ratio(country_code, start_date, end_date)
        df_total_accumulated = pd.DataFrame(
            columns=["simulation_time", "imported_from_grid", "imported_from_community"]
        )
        for area in imported_exported_energy.values():
            for timestamp, imported_energy in area.items():
                df_imported_energy = pd.DataFrame(
                    {
                        "simulation_time": pd.to_datetime(timestamp).tz_localize("UTC"),
                        "imported_from_grid": imported_energy["imported_from_grid"],
                        "imported_from_community": imported_energy["imported_from_community"],
                    },
                    index=[0],
                )
                df_total_accumulated = (
                    pd.concat([df_total_accumulated, df_imported_energy])
                    .groupby("simulation_time", as_index=False)
                    .sum()
                )
        df_carbon_emissions = self.calculate_from_carbon_ratio_and_imported_energy(
            df_carbon_ratio, df_total_accumulated
        )
        total_emissions = df_carbon_emissions.drop(columns=["simulation_time"]).sum().to_dict()
        return total_emissions
