import abc
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Any

from pendulum import DateTime
from gsy_framework.read_user_profile import resample_hourly_energy_profile


@dataclass
class PvApiParameters:
    """
    Parameters that contains all PV settings that are needed for external PV profile APIs
        longitude: longitude of the PV location
        latitude: latitude of the PV location
        capacity_kW: base pv production in kW that is used to scale the data on the API side
        azimuth: orientation of the PV (cardinal direction)
        tilt: tilt of the PV panel WRT to the vertical axis (e.g. inclination of the roof)
    """
    latitude: float
    longitude: float
    capacity_kW: float
    azimuth: float
    tilt: float


class SolarAPIClientBase(abc.ABC):
    """Baseclass for all solar api clients."""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_solar_energy_profile(
            self, request_parameters: PvApiParameters, start_date: DateTime, end_date: DateTime,
            slot_length: timedelta) -> Dict[DateTime, float]:
        """Request energy profile from external solar API.

        return: Dictionary of raw data including a time series of energy production with
                resolution of 1 hour.
        """
        raw_data = self._request_raw_solar_energy_data(
            request_parameters,
            self._get_corresponding_historical_time_stamp(start_date),
            self._get_corresponding_historical_time_stamp(end_date))
        energy_profile = self._create_time_series_from_solar_profile(
            raw_data, start_date.year, end_date.year)
        resampled_profile = resample_hourly_energy_profile(
            energy_profile, slot_length, end_date - start_date, start_date)
        return resampled_profile

    @staticmethod
    @abc.abstractmethod
    def _get_corresponding_historical_time_stamp(input_datetime: DateTime) -> DateTime:
        """
        Return the corresponding historical time stamp that is different for each API client.
        Due to the different data availability of different sources, the requested year
        needs to be altered in order to request historical data that is available. Leap years have
        to be considered.
        """

    @abc.abstractmethod
    def _request_raw_solar_energy_data(self, request_parameters: PvApiParameters,
                                       start_date: DateTime, end_date: DateTime) -> Any:
        """
        Perform the actual request to the API and return raw data in the API specific format.
        """

    @staticmethod
    @abc.abstractmethod
    def _create_time_series_from_solar_profile(request_data: Dict,
                                               out_start_year: int,
                                               out_end_year: int) -> Dict[DateTime, float]:
        """
        Convert the API specific data into a time series dict that can be digested by gsy-web.
        """
