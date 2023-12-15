# pylint: disable=invalid-name
import logging
from typing import Dict

import requests
from pendulum import from_format, DateTime, today
from gsy_framework.constants_limits import TIME_ZONE

from gsy_framework.solar_api_clients.api_client_base import SolarAPIClientBase, PvApiParameters


class SolarAPIClientActiveException(Exception):
    """Exception for active solar api client"""


TIME_OUTPUT_FORMAT = "YYYY-MM-DDTHH:mm:ss+00:00"
TIME_INPUT_FORMAT = "YYYY-MM-DD"
NORMAL_YEAR = 2019
LEAP_YEAR = 2020
FIRST_AVAILABLE_YEAR = 1979


class SolarAPIClientActive(SolarAPIClientBase):
    """ETL for energy data from active solar API."""

    @staticmethod
    def _get_corresponding_historical_time_stamp(input_datetime: DateTime) -> DateTime:
        """
        Substitute the year of the input_datetime with the leap/normal years used as reference.
        """
        if ((input_datetime.year >= today().year) or
                (input_datetime.year < FIRST_AVAILABLE_YEAR)):
            # if the user request pseudo-future data, use historical years
            request_year = (LEAP_YEAR
                            if input_datetime.is_leap_year() else NORMAL_YEAR)
            output_datetime = input_datetime.set(year=request_year)
        else:
            output_datetime = input_datetime
        return output_datetime

    def _request_raw_solar_energy_data(self, request_parameters: PvApiParameters,
                                       start_date: DateTime,
                                       end_date: DateTime) -> Dict:
        """Request energy profile from API.

        return: Dictionary of raw data including a time series of energy production with
                resolution of 1 hour.
        """
        payload = {"longitude": request_parameters.longitude,
                   "latitude": request_parameters.latitude,
                   "capacity_kw": request_parameters.capacity_kW,
                   "azimuth": request_parameters.azimuth,
                   "tilt": request_parameters.tilt,
                   "frequency": "1h",  # never change this in order to receive energy values
                   "start_date": start_date.format(TIME_INPUT_FORMAT),
                   "end_date": end_date.format(TIME_INPUT_FORMAT)
                   }

        try:
            response = requests.get(self.api_url, params=payload,
                                    timeout=30)
        except requests.exceptions.RequestException as ex:
            error_message = ("An error happened when requesting solar energy profile from "
                             f"active solar API: {ex}")
            logging.error(error_message)
            raise SolarAPIClientActiveException(error_message) from ex

        if response.status_code != 200:
            error_message = ("An error happened when requesting solar energy profile from "
                             f"active solar API: status_code = {response.status_code}")
            raise SolarAPIClientActiveException(error_message)

        return response.json()

    @staticmethod
    def _create_time_series_from_solar_profile(request_data: Dict,
                                               out_start_year: int,
                                               out_end_year: int) -> Dict[DateTime, float]:
        """
        Convert time stamps back to DateTime and change requested years back to the buffer values.
        """
        try:
            out_dict = {}
            for index, energy in enumerate(request_data["Physical_Forecast"]):
                time_key = from_format(request_data["valid_datetime"][index],
                                       TIME_OUTPUT_FORMAT, tz=TIME_ZONE)
                if time_key.year == LEAP_YEAR:
                    out_year = out_start_year
                elif time_key.year == NORMAL_YEAR:
                    out_year = out_end_year
                else:
                    error_message = f"Unexpected year value for {time_key}"
                    logging.error(error_message)
                    assert False, error_message
                out_dict[time_key.set(year=out_year)] = energy
            return out_dict

        except Exception as error:
            raise SolarAPIClientActiveException("Something went wrong while converting "
                                                "active solar API data to GSy-compatible: "
                                                f"{error}.") from error
