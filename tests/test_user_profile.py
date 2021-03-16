"""
Copyright 2018 Grid Singularity
This file is part of D3A.

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
import unittest
from pendulum import datetime, duration
from d3a_interface.unit_test_utils import assert_dicts_identical
from d3a_interface.read_user_profile import _generate_slot_based_zero_values_dict_from_profile, \
    _fill_gaps_in_profile, _interpolate_profile_values_to_slot, read_profile_for_player


class TestReadUserProfile(unittest.TestCase):

    def _validate_timedeltas_are_followed(self, profile):
        timestamps_list = list(profile.keys())
        assert timestamps_list[0] == datetime(2021, 2, 12, 0, 0, 0)
        assert timestamps_list[-1] == datetime(2021, 2, 14, 23, 45, 0)

        for index, t in enumerate(timestamps_list):
            if index + 1 < len(timestamps_list):
                assert timestamps_list[index + 1] - t == duration(minutes=15)

    def test_generate_slot_based_zero_values_dict_from_profile(self):
        profile_dict = {
            datetime(2021, 2, 12, 0, 12, 10): 1234.0,
            datetime(2021, 2, 14, 23, 55, 10): 1234.0
        }
        zero_val_dict = _generate_slot_based_zero_values_dict_from_profile(profile_dict)
        assert all(v == 0.0 for v in zero_val_dict.values())
        self._validate_timedeltas_are_followed(zero_val_dict)

    def test_fill_gaps_in_profile(self):
        profile_dict = {
            datetime(2021, 2, 12, 0, 0, 0): 1234.0,
            datetime(2021, 2, 14, 23, 55, 10): 1234.0
        }
        zero_val_dict = _generate_slot_based_zero_values_dict_from_profile(profile_dict)
        filled_profile = _fill_gaps_in_profile(profile_dict, zero_val_dict)
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
            datetime(2021, 2, 12, 0, 30, 0): 100.0
        }

        interp_profile, slot_times = _interpolate_profile_values_to_slot(profile_dict, duration(minutes=15))
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
            datetime(2021, 2, 12, 0, 30, 0): 100.0
        }
        return_dict = read_profile_for_player(profile_dict)

        assert len(return_dict.keys()) == 3
        assert_dicts_identical(return_dict, {
            datetime(2021, 2, 12, 0, 0, 0): 0.15,
            datetime(2021, 2, 12, 0, 15, 0): 0.5,
            datetime(2021, 2, 12, 0, 30, 0): 0.1
        })
