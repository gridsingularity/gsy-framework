"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import pytest
from pendulum import datetime, duration, today

from gsy_framework.constants_limits import TIME_ZONE, GlobalConfig
from gsy_framework.enums import ConfigurationType
from gsy_framework.read_user_profile import InputProfileTypes, UserProfileReader
from gsy_framework.unit_test_utils import assert_dicts_identical
from gsy_framework.utils import convert_str_to_pendulum_in_dict


@pytest.fixture(name="set_is_canary_network")
def set_is_canary_network_fixture():
    """Change the GlobalConfig value and then restore it at the end of the test."""
    original_value = None

    def _setup(value):
        nonlocal original_value
        original_value = GlobalConfig.CONFIG_TYPE
        GlobalConfig.CONFIG_TYPE = (
            ConfigurationType.CANARY_NETWORK.value if value else ConfigurationType.SIMULATION.value
        )

    yield _setup
    GlobalConfig.CONFIG_TYPE = original_value


# pylint: disable=protected-access
class TestReadUserProfile:
    """Test reading the user profiles."""

    def setup_method(self):
        # pylint: disable=attribute-defined-outside-init
        self._profile = UserProfileReader()

    @staticmethod
    def _validate_timedeltas_are_followed(profile):
        timestamps_list = list(profile.keys())
        assert timestamps_list[0] == datetime(2021, 2, 12, 0, 0, 0)
        assert timestamps_list[-1] == datetime(2021, 2, 14, 23, 45, 0)

        for index, timestamp in enumerate(timestamps_list):
            if index + 1 < len(timestamps_list):
                assert timestamps_list[index + 1] - timestamp == duration(minutes=15)

    def test_generate_slot_based_zero_values_dict_from_profile(self):
        profile_dict = {
            datetime(2021, 2, 12, 0, 12, 10): 1234.0,
            datetime(2021, 2, 14, 23, 55, 10): 1234.0,
        }
        zero_val_dict = self._profile._generate_slot_based_zero_values_dict_from_profile(
            profile_dict
        )
        assert all(v == 0.0 for v in zero_val_dict.values())
        self._validate_timedeltas_are_followed(zero_val_dict)

    def test_fill_gaps_in_profile(self):
        profile_dict = {
            datetime(2021, 2, 12, 0, 0, 0): 1234.0,
            datetime(2021, 2, 14, 23, 55, 10): 1234.0,
        }
        zero_val_dict = self._profile._generate_slot_based_zero_values_dict_from_profile(
            profile_dict
        )
        filled_profile = self._profile._fill_gaps_in_profile(profile_dict, zero_val_dict)
        assert all(v == 1234.0 for v in filled_profile.values())
        self._validate_timedeltas_are_followed(filled_profile)

    def test_interpolate_profile_values_to_slot(self):
        profile_dict = {
            datetime(2021, 2, 12, 0, 0, 0): 150.0,
            datetime(2021, 2, 12, 0, 5, 0): 100.0,
            datetime(2021, 2, 12, 0, 10, 0): 200.0,
            datetime(2021, 2, 12, 0, 15, 0): 500.0,
            datetime(2021, 2, 12, 0, 20, 0): 700.0,
            datetime(2021, 2, 12, 0, 25, 0): 600.0,
            datetime(2021, 2, 12, 0, 30, 0): 100.0,
        }

        interp_profile, slot_times = self._profile._interpolate_profile_values_to_slot(
            profile_dict, duration(minutes=15)
        )
        assert len(interp_profile) == 3
        assert slot_times[0] == datetime(2021, 2, 12, 0, 0, 0).timestamp()
        assert slot_times[1] == datetime(2021, 2, 12, 0, 15, 0).timestamp()
        assert slot_times[2] == datetime(2021, 2, 12, 0, 30, 0).timestamp()
        assert interp_profile[0] == 0.15
        assert interp_profile[1] == 0.5
        assert interp_profile[2] == 0.1

    def test_read_profile_for_player(self):
        profile_dict = {
            datetime(2021, 2, 12, 0, 0, 0): 150.0,
            datetime(2021, 2, 12, 0, 5, 0): 100.0,
            datetime(2021, 2, 12, 0, 10, 0): 200.0,
            datetime(2021, 2, 12, 0, 15, 0): 500.0,
            datetime(2021, 2, 12, 0, 20, 0): 700.0,
            datetime(2021, 2, 12, 0, 25, 0): 600.0,
            datetime(2021, 2, 12, 0, 30, 0): 100.0,
        }
        return_dict = self._profile.read_profile_without_config(profile_dict)

        assert len(return_dict.keys()) == 3
        assert_dicts_identical(
            return_dict,
            {
                datetime(2021, 2, 12, 0, 0, 0): 0.15,
                datetime(2021, 2, 12, 0, 15, 0): 0.5,
                datetime(2021, 2, 12, 0, 30, 0): 0.1,
            },
        )

    def test_read_arbitrary_profile_returns_correct_profile_in_canary_network(
        self, set_is_canary_network
    ):
        set_is_canary_network(True)
        expected_last_time_slot = today(tz=TIME_ZONE)
        mmr = self._profile.read_arbitrary_profile(InputProfileTypes.IDENTITY, 30)
        assert list(mmr.keys())[-1] == expected_last_time_slot

    def test_read_arbitrary_profile_returns_correct_profile(self, set_is_canary_network):
        set_is_canary_network(False)
        market_maker_rate = 30
        GlobalConfig.FUTURE_MARKET_DURATION_HOURS = 0
        GlobalConfig.sim_duration = duration(hours=3)
        mmr = self._profile.read_arbitrary_profile(InputProfileTypes.IDENTITY, market_maker_rate)
        assert (list(mmr.keys())[-1] - today(tz=TIME_ZONE)).days == 0
        GlobalConfig.sim_duration = duration(hours=36)
        mmr = self._profile.read_arbitrary_profile(InputProfileTypes.IDENTITY, market_maker_rate)
        assert (list(mmr.keys())[-1] - today(tz=TIME_ZONE)).days == 1

        GlobalConfig.FUTURE_MARKET_DURATION_HOURS = 24
        GlobalConfig.sim_duration = duration(hours=1)
        mmr = self._profile.read_arbitrary_profile(InputProfileTypes.IDENTITY, market_maker_rate)
        time_diff = list(mmr.keys())[-1] - today(tz=TIME_ZONE)
        assert time_diff.minutes == 45

    def test_resample_energy_profile_performs_correctly_for_lower_resolutions(self):
        input_profile = {
            "2021-01-25T00:00": 0.1,
            "2021-01-25T01:00": 0.1,
            "2021-01-25T02:00": 0.1,
            "2021-01-25T03:00": 0.1,
            "2021-01-25T04:00": 0.1,
        }
        result_profile = self._profile.resample_hourly_energy_profile(
            convert_str_to_pendulum_in_dict(input_profile),
            duration(minutes=15),
            duration(hours=4),
            datetime(2021, 1, 25, 0, 0),
        )
        assert len(result_profile) == 16
        first_time_stamp = next(iter(result_profile))
        last_time_stamp = next(reversed(result_profile))
        assert first_time_stamp == datetime(2021, 1, 25, 0, 0)
        assert last_time_stamp == datetime(2021, 1, 25, 3, 45)
        assert all(value == 0.025 for value in result_profile.values())

    def test_resample_energy_profile_performs_correctly_for_higher_resolutions(self):
        input_profile = {
            "2021-01-25T00:00": 0.1,
            "2021-01-25T01:00": 0.1,
            "2021-01-25T02:00": 0.1,
            "2021-01-25T03:00": 0.1,
            "2021-01-25T04:00": 0.1,
            "2021-01-25T05:00": 0.1,
            "2021-01-25T06:00": 0.1,
        }
        result_profile = self._profile.resample_hourly_energy_profile(
            convert_str_to_pendulum_in_dict(input_profile),
            duration(hours=2),
            duration(hours=6),
            datetime(2021, 1, 25, 0, 0),
        )
        assert result_profile == {
            datetime(2021, 1, 25, 0, 0, 0): 0.2,
            datetime(2021, 1, 25, 2, 0, 0): 0.2,
            datetime(2021, 1, 25, 4, 0, 0): 0.2,
        }

    def test_resample_energy_profile_performs_correctly_for_equal_resolutions(self):
        input_profile = {
            "2021-01-25T00:00": 0.1,
            "2021-01-25T01:00": 0.1,
            "2021-01-25T02:00": 0.1,
            "2021-01-25T03:00": 0.1,
            "2021-01-25T04:00": 0.1,
        }
        input_profile = convert_str_to_pendulum_in_dict(input_profile)
        result_profile = self._profile.resample_hourly_energy_profile(
            input_profile, duration(minutes=60), duration(hours=4), datetime(2021, 1, 25, 0, 0)
        )
        assert result_profile == input_profile

    def test_read_arbitrary_profile_returns_early_for_empty_profiles(self):
        original_slot_length = GlobalConfig.slot_length
        original_sim_duration = GlobalConfig.sim_duration
        GlobalConfig.slot_length = duration(hours=1)
        GlobalConfig.sim_duration = duration(hours=4)
        assert self._profile.read_arbitrary_profile(InputProfileTypes.POWER_W, {}) == {}
        assert self._profile.read_arbitrary_profile(InputProfileTypes.POWER_W, None) == {}
        assert len(self._profile.read_arbitrary_profile(InputProfileTypes.POWER_W, 0)) == 4
        assert set(
            self._profile.read_arbitrary_profile(InputProfileTypes.POWER_W, 0).values()
        ) == {0}
        GlobalConfig.slot_length = original_slot_length
        GlobalConfig.sim_duration = original_sim_duration
