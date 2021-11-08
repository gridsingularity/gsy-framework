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
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
from unittest.mock import patch, MagicMock

import pytest
from pendulum import datetime, today

from d3a_interface.utils import (datetime_to_string_incl_seconds,
                                 HomeRepresentationUtils, convert_datetime_to_ui_str_format,
                                 execute_function_util, scenario_representation_traversal,
                                 sort_list_of_dicts_by_attribute, str_to_pendulum_datetime)


@pytest.fixture(name="scenario_repr")
def scenario_repr_fixture():
    return {
            "name": "grid",
            "children": [
                {"name": "S1 House", "children": [
                    {"name": "Load", "type": "Load"},
                    {"name": "Home Battery", "type": "Storage"}
                ]},
                {"name": "S2 House", "children": [
                    {"name": "Load", "type": "Load"},
                    {"name": "Home Battery", "type": "Storage"},
                    {"name": "Home PV", "type": "PV"}
                ]}
            ]
        }


class TestUtils:

    @staticmethod
    def test_scenario_representation_traversal(scenario_repr):
        areas = list(scenario_representation_traversal(scenario_repr))
        assert len(areas) == 8
        assert all(isinstance(obj, tuple) for obj in areas)

    @staticmethod
    def test_calculate_home_area_stats_from_repr_dict(scenario_repr):
        home_count, avg_devices_per_home = \
            HomeRepresentationUtils.calculate_home_area_stats_from_repr_dict(scenario_repr)
        assert home_count == 2
        assert avg_devices_per_home == 2.5

    @staticmethod
    def test_sort_list_of_dicts_by_attribute():
        input_list = [
            {"id": 1, "energy": 15, "energy_rate": 1, "price": 30},
            {"id": 2, "energy": 20, "energy_rate": 4, "price": 25},
            {"id": 3, "energy": 12, "energy_rate": 3, "price": 77},
            {"id": 4, "energy": 13, "energy_rate": 2, "price": 12},
        ]
        output_list = sort_list_of_dicts_by_attribute(input_list, "price")
        assert [4, 2, 1, 3] == [data["id"] for data in output_list]
        output_list = sort_list_of_dicts_by_attribute(input_list, "price", reverse_order=True)
        assert [3, 1, 2, 4] == [data["id"] for data in output_list]

    @staticmethod
    def test_convert_datetime_to_ui_str_format():
        current_time = datetime(year=2021, month=8, day=30, hour=15, minute=30, second=45)
        current_time_str = convert_datetime_to_ui_str_format(current_time)
        assert current_time_str == "August 30 2021, 15:30 h"

    @staticmethod
    def test_str_to_pendulum_datetime():
        datetime_obj = datetime(year=2021, month=4, day=5, hour=12, minute=30)
        assert str_to_pendulum_datetime("2021-04-05T12:30") == datetime_obj
        assert str_to_pendulum_datetime("2021-04-05T12:30:00") == datetime_obj
        datetime_obj = today(tz="UTC")
        datetime_obj = datetime_obj.set(hour=12, minute=30)
        assert str_to_pendulum_datetime("12:30") == datetime_obj
        assert str_to_pendulum_datetime("12:30:00") == datetime_obj
        with pytest.raises(Exception):
            str_to_pendulum_datetime("an_erroneous_datetime_string")
        with pytest.raises(Exception):
            str_to_pendulum_datetime("2021-04-05T12:30:00-04:00")

    @staticmethod
    def test_datetime_to_string_incl_seconds():
        """Test if datetime_to_string_incl_seconds returns correctly."""
        assert (datetime_to_string_incl_seconds(date_time=datetime(2021, 11, 4, 15, 30)) ==
                "2021-11-04T15:30:00")

    @staticmethod
    @patch("d3a_interface.utils.logging")
    def test_execute_function_util_logs_raised_exceptions(logging_mock: MagicMock):
        """The execute_function_util correctly logs exceptions when they are raised."""
        raised_exception = ValueError("some exception message")
        function_mock = MagicMock(side_effect=raised_exception)
        execute_function_util(function_mock, function_name="function_mock_name")

        logging_mock.exception.assert_called_once_with(
            "%s raised exception: %s.", "function_mock_name", raised_exception)
