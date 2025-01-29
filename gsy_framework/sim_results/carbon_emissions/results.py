from typing import Union, Dict, List, Tuple
from datetime import datetime

import pytz

import requests
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.mappings import lookup_area, Area
from entsoe.parsers import parse_generation
from geopy.geocoders import Nominatim
from iso3166 import countries

from gsy_framework.constants_limits import DATE_TIME_FORMAT
from gsy_framework.sim_results.carbon_emissions.constants import (
    ENTSOE_URL,
    GENERATION_PLANT_TO_CARBON_EMISSIONS,
    GEOPY_TO_ENTSOE_COUNTRY_CODE,
    MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES,
    Stat,
)
from gsy_framework.sim_results.carbon_emissions.exceptions import EntsoeDataLimitExceededError


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
        if "The amount of requested data exceeds allowed limit." in text:
            raise EntsoeDataLimitExceededError(
                "The amount of requested data exceeds allowed limit."
            )

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

    def _find_start_and_end_dates(
        self, dates: List, datetime_format: str = DATE_TIME_FORMAT
    ) -> Tuple[datetime, datetime]:
        """Find the start and end dates from a list of string timestamps"""

        dates = [datetime.strptime(timestr, datetime_format) for timestr in dates]
        start_date = min(dates).replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0)
        end_date = max(dates).replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0)
        return start_date, end_date

    def _query_from_entsoe(
        self, country_code: str, start: pd.Timestamp, end: pd.Timestamp, stat: Stat = Stat.MEDIAN
    ):
        """Query generation per plant from the Entsoe API"""
        entsoe_client = EntsoePandasClientAdapter(api_key=self.entsoe_api_key)
        country_code = GEOPY_TO_ENTSOE_COUNTRY_CODE[country_code]
        df_generation_per_plant = entsoe_client._query_generation_per_plant(
            country_code, start, end
        )  # example: https://transparency.entsoe.eu/generation/r2/actualGenerationPerGenerationUnit/show?name=&defaultValue=true&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=01.01.2024+00:00|UTC|DAYTIMERANGE&dateTime.endDateTime=01.01.2024+00:00|UTC|DAYTIMERANGE&area.values=CTY|10YSE-1--------K!BZN|10Y1001A1001A44P&masterDataFilterName=&masterDataFilterCode=&productionType.values=B01&productionType.values=B25&productionType.values=B02&productionType.values=B03&productionType.values=B04&productionType.values=B05&productionType.values=B06&productionType.values=B07&productionType.values=B08&productionType.values=B09&productionType.values=B10&productionType.values=B11&productionType.values=B12&productionType.values=B13&productionType.values=B14&productionType.values=B20&productionType.values=B15&productionType.values=B16&productionType.values=B17&productionType.values=B18&productionType.values=B19&dateTime.timezone=UTC&dateTime.timezone_input=UTC&dv-datatable_length=50  # noqa

        # df_generation_per_plant is a MultiIndex DataFrame
        generation_types = df_generation_per_plant.columns.get_level_values(1)
        emissions_map = pd.Series(
            [
                GENERATION_PLANT_TO_CARBON_EMISSIONS[generation_type][stat]
                for generation_type in generation_types
            ],
            index=df_generation_per_plant.columns,  # Map emissions to columns
        )
        df_numeric = df_generation_per_plant.iloc[1:].apply(pd.to_numeric, errors="coerce")
        df_numeric.index = pd.to_datetime(df_numeric.index, utc=True)

        df_numeric["Total Energy (kWh)"] = df_numeric.sum(axis=1)  # convert from MW to kWh
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
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start and end must have timezone")
        if start.utcoffset() != pd.Timedelta(0) or end.utcoffset() != pd.Timedelta(0):
            raise ValueError("start and end must be in UTC+0")

        if (
            country_code in GEOPY_TO_ENTSOE_COUNTRY_CODE
        ):  # source: https://transparency.entsoe.eu/)
            try:
                df_carbon_ratio = self._query_from_entsoe(country_code, start, end, stat)
            except EntsoeDataLimitExceededError:
                df_carbon_ratio = pd.DataFrame()
                days_range = pd.date_range(start, end, freq="H")
                for day in days_range.to_period("D").unique():
                    df_daily = self._query_from_entsoe(
                        country_code, day.start_time, day.end_time, stat
                    )
                    df_carbon_ratio = pd.concat([df_carbon_ratio, df_daily])
        elif (
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
