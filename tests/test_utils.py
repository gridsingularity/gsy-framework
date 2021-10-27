from unittest.mock import patch, MagicMock

import pytest
from pendulum import datetime, today

from gsy_framework.utils import (
    HomeRepresentationUtils, convert_datetime_to_ui_str_format, execute_function_util,
    scenario_representation_traversal, sort_list_of_dicts_by_attribute, str_to_pendulum_datetime)


class TestUtils:
    def setup_method(self):
        self.scenario_repr = {
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

    def test_scenario_representation_traversal(self):
        areas = list(scenario_representation_traversal(self.scenario_repr))
        assert len(areas) == 8
        assert all(type(obj) == tuple for obj in areas)

    def test_calculate_home_area_stats_from_repr_dict(self):
        home_count, avg_devices_per_home = \
            HomeRepresentationUtils.calculate_home_area_stats_from_repr_dict(self.scenario_repr)
        assert home_count == 2
        assert avg_devices_per_home == 2.5

    def test_sort_list_of_dicts_by_attribute(self):
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

    def test_convert_datetime_to_ui_str_format(self):
        current_time = datetime(year=2021, month=8, day=30, hour=15, minute=30, second=45)
        current_time_str = convert_datetime_to_ui_str_format(current_time)
        assert current_time_str == "August 30 2021, 15:30 h"

    def test_str_to_pendulum_datetime(self):
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
    @patch("gsy_framework.utils.logging")
    def test_execute_function_util_logs_raised_exceptions(logging_mock: MagicMock):
        """The execute_function_util correctly logs exceptions when they are raised."""
        raised_exception = ValueError("some exception message")
        function_mock = MagicMock(side_effect=raised_exception)
        execute_function_util(function_mock, function_name="function_mock_name")

        logging_mock.exception.assert_called_once_with(
            "%s raised exception: %s.", "function_mock_name", raised_exception)
