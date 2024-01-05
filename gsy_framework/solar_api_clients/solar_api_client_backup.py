# pylint: disable=invalid-name
from typing import Dict, Any

import pendulum
import requests
from pendulum import DateTime
from gsy_framework.constants_limits import TIME_ZONE

from gsy_framework.solar_api_clients.api_client_base import SolarAPIClientBase, PvApiParameters

LEAP_YEAR = 2016
NORMAL_YEAR = 2015
TIME_OUTPUT_FORMAT = "YYYYMMDD:HHmm"


class SolarAPIClientBackupException(Exception):
    """Exception for backup solar api client"""


class SolarAPIClientBackup(SolarAPIClientBase):
    """ETL for energy data from backup solar API."""

    @staticmethod
    def _get_corresponding_historical_time_stamp(input_datetime: DateTime) -> DateTime:

        request_year = (LEAP_YEAR
                        if input_datetime.is_leap_year() else NORMAL_YEAR)
        output_datetime = input_datetime.set(year=request_year)
        return output_datetime

    def _request_raw_solar_energy_data(
            self, request_parameters: PvApiParameters, start_date: DateTime, end_date: DateTime
    ) -> Any:
        try:
            params = {"lat": request_parameters.latitude,
                      "lon": request_parameters.longitude,
                      "outputformat": "json",
                      "angle": request_parameters.tilt,
                      "aspect": request_parameters.azimuth - 180,
                      "pvcalculation": 1,
                      "pvtechchoice": "crystSi",
                      "mountingplace": "free",
                      "trackingtype": 0,
                      "components": 0,
                      "usehorizon": 1,
                      "optimalangles": 0,
                      "optimalinclination": 0,
                      "loss": 0,
                      "peakpower": request_parameters.capacity_kW,
                      "startyear": start_date.year,
                      "endyear": end_date.year}

            res = requests.get(self.api_url, params=params, timeout=30)
            return res.json()

        except Exception as ex:
            raise SolarAPIClientBackupException from ex

    @staticmethod
    def _create_time_series_from_solar_profile(request_data: Dict,
                                               out_start_year: int,
                                               out_end_year: int) -> Dict[DateTime, float]:
        out_dict = {}
        for dp in request_data["outputs"]["hourly"]:
            time_key = pendulum.from_format(dp["time"], TIME_OUTPUT_FORMAT, tz=TIME_ZONE)
            if time_key.year == LEAP_YEAR:
                out_year = out_start_year
            elif time_key.year == NORMAL_YEAR:
                out_year = out_end_year
            else:
                error_message = f"Unexpected year value for {time_key}"
                assert False, error_message
            out_dict[time_key.set(year=out_year, minute=0)] = dp["P"] / 1000
        return out_dict
