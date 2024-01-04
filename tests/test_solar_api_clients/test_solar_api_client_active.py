from typing import Dict
from unittest.mock import patch

import pytest
import requests
from pendulum import datetime, DateTime, duration

from gsy_framework.solar_api_clients.solar_api_client_active import (SolarAPIClientActive,
                                                                     PvApiParameters,
                                                                     SolarAPIClientActiveException,
                                                                     TIME_INPUT_FORMAT,
                                                                     TIME_OUTPUT_FORMAT)

API_URL = "http://active.solar.api"
DEFAULT_LON = 52.5170
DEFAULT_LAT = 13.3889
DEFAULT_AZI = 180
DEFAULT_CAPACITY = 1
DEFAULT_TILT = 35


@pytest.fixture(name="default_request_parameters")
def default_pv_api_param_fixture():
    """Create a default pv config as input for the SolarAPIClientActive."""
    return PvApiParameters(latitude=DEFAULT_LAT, longitude=DEFAULT_LON,
                           capacity_kW=DEFAULT_CAPACITY, azimuth=DEFAULT_AZI, tilt=DEFAULT_TILT)


def mock_api_ret_val_data(start_time: DateTime, end_time: DateTime) -> Dict:
    """Create a mock of the return value of the active solar api."""
    default_dict = {"valid_datetime": [],
                    "Clearsky_Forecast": [],
                    "Physical_Forecast": []}

    current_time = start_time
    while current_time <= end_time:
        default_dict["valid_datetime"].append(current_time.format(TIME_OUTPUT_FORMAT))
        default_dict["Clearsky_Forecast"].append(1)
        default_dict["Physical_Forecast"].append(0.5)
        current_time = current_time.add(hours=1)
    return default_dict


def mock_api_url(start_time: DateTime, end_time: DateTime) -> str:
    """Create a url that represents a valid call to the SolarAPIClientActive."""
    return (f"{API_URL}?"
            f"&longitude={DEFAULT_LON}"
            f"&latitude={DEFAULT_LAT}"
            f"&capacity_kw={DEFAULT_CAPACITY}"
            f"&azimuth={DEFAULT_AZI}"
            f"&tilt={DEFAULT_TILT}"
            f"&start_date={start_time.format(TIME_INPUT_FORMAT)}"
            f"&end_date={end_time.format(TIME_INPUT_FORMAT)}"
            )


class TestSolarAPIClientActive:
    """Collection of tests targeting the SolarAPIClientActive."""

    @staticmethod
    def test_get_solar_power_profile_raises_error_if_status_not_200(requests_mock,
                                                                    default_request_parameters):
        """Test if Exception is raised if active solar api does not return http code 200."""
        requests_mock.get(API_URL, status_code=404)
        with pytest.raises(SolarAPIClientActiveException):
            SolarAPIClientActive(API_URL).get_solar_energy_profile(default_request_parameters,
                                                                   datetime(2016, 8, 4),
                                                                   datetime(2016, 8, 5),
                                                                   duration(minutes=15))

    @staticmethod
    def test_get_solar_power_profile_re_raises_requests_exception(requests_mock,
                                                                  default_request_parameters):
        """Test if SolarAPIClientActive re-raises exception from requests."""
        requests_mock.get(API_URL,
                          exc=requests.exceptions.ConnectTimeout)
        with pytest.raises(SolarAPIClientActiveException):
            SolarAPIClientActive(API_URL).get_solar_energy_profile(default_request_parameters,
                                                                   datetime(2016, 8, 4),
                                                                   datetime(2016, 8, 5),
                                                                   duration(minutes=15))

    @staticmethod
    @patch("gsy_framework.solar_api_clients.solar_api_client_active.today",
           lambda: datetime(2023, 1, 1))
    @pytest.mark.parametrize("requested_year, api_output_year", [
        (2024, 2020),
        (2023, 2019),
        (2020, 2020)
    ])
    def test_get_solar_power_profile_returns_correct_years(
            requests_mock, default_request_parameters, requested_year, api_output_year):
        """Test if get_solar_power_profile returns data with correct time stamps."""
        api_output_start_date = datetime(api_output_year, 8, 4, 0)
        api_output_end_date = datetime(api_output_year, 8, 5, 23)
        requests_mock.get(
            url=mock_api_url(api_output_start_date,
                             api_output_end_date),
            json=mock_api_ret_val_data(api_output_start_date,
                                       api_output_end_date))

        profile = SolarAPIClientActive(API_URL).get_solar_energy_profile(
            default_request_parameters,
            datetime(requested_year, 8, 4),
            datetime(requested_year, 8, 5),
            duration(minutes=60))
        assert len(profile.keys()) == 48
        assert all(time.year == requested_year for time in profile)

    @staticmethod
    def test_get_solar_power_profile_returns_correct_years_mixed(
            requests_mock, default_request_parameters):
        """
            Test if get_solar_power_profile returns data with correct time stamps also for a
            two different years in the requested time frame.
        """
        api_output_start_date = datetime(2019, 12, 31, 0)
        api_output_end_date = datetime(2020, 1, 1, 23)
        requests_mock.get(
            url=mock_api_url(api_output_start_date,
                             api_output_end_date),
            json=mock_api_ret_val_data(api_output_start_date,
                                       api_output_end_date))

        profile = SolarAPIClientActive(API_URL).get_solar_energy_profile(
            default_request_parameters,
            datetime(2019, 12, 31),
            datetime(2020, 1, 1, ),
            duration(minutes=60))
        assert len(profile.keys()) == 48
        assert len([time for time in profile if time.year == 2019]) == 24
        assert len([time for time in profile if time.year == 2020]) == 24

    @staticmethod
    def test_get_solar_power_profile_api_returns_wrong_years(requests_mock,
                                                             default_request_parameters):
        """Test if exception is raised if active solar Api returns wrong time stamps."""
        requests_mock.get(
            url=mock_api_url(datetime(2019, 12, 31, 0),
                             datetime(2020, 1, 1, 23)),
            json=mock_api_ret_val_data(datetime(1998, 12, 31, 0),
                                       datetime(1999, 1, 1, 23)))
        with pytest.raises(SolarAPIClientActiveException):
            SolarAPIClientActive(API_URL).get_solar_energy_profile(default_request_parameters,
                                                                   datetime(2019, 12, 31),
                                                                   datetime(2020, 1, 1),
                                                                   duration(minutes=15))
