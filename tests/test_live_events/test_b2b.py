from copy import deepcopy

import pytest

from gsy_framework.live_events.b2b import LiveEventArgsValidator

correct_args = {
    "start_time": "2022-01-01T12:30",
    "end_time": "2022-01-01T12:30",
    "capacity_percent": 100.0,
    "energy_rate": 12.0,
    "market_type": 4
}


class TestB2BLiveEvents:

    @staticmethod
    @pytest.mark.parametrize("validate_method, arguments", [
        (LiveEventArgsValidator(lambda x, y: None).are_start_trading_event_args_valid,
         ["start_time", "end_time", "market_type", "capacity_percent", "energy_rate"]),
        (LiveEventArgsValidator(lambda x, y: None).are_stop_trading_event_args_valid,
         ["start_time", "end_time", "market_type"]),
    ])
    def test_validate_start_trading_missing_args(validate_method, arguments):
        method_arguments = {k: v for k, v in correct_args.items() if k in arguments}
        assert validate_method(method_arguments) is True
        for arg_name in arguments:
            args_copy = deepcopy(method_arguments)
            args_copy.pop(arg_name)
            assert validate_method(args_copy) is False

    @staticmethod
    def test_validate_capacity_percent():
        validator = LiveEventArgsValidator(lambda x, y: None)
        args_copy = deepcopy(correct_args)
        args_copy["capacity_percent"] = -12.0
        assert validator.are_start_trading_event_args_valid(args_copy) is False
        args_copy["capacity_percent"] = 123.0
        assert validator.are_start_trading_event_args_valid(args_copy) is False
        args_copy["capacity_percent"] = 99.0
        assert validator.are_start_trading_event_args_valid(args_copy) is True

    @staticmethod
    def test_validate_energy_rate():
        validator = LiveEventArgsValidator(lambda x, y: None)
        args_copy = deepcopy(correct_args)
        args_copy["energy_rate"] = -1.0
        assert validator.are_start_trading_event_args_valid(args_copy) is False
        args_copy["energy_rate"] = 1.0
        assert validator.are_start_trading_event_args_valid(args_copy) is True

    @staticmethod
    @pytest.mark.parametrize("time_parameter_name", ["start_time", "end_time"])
    def test_validate_start_end_time_on_start_trading(time_parameter_name):
        validator = LiveEventArgsValidator(lambda x, y: None)
        args_copy = deepcopy(correct_args)
        assert validator.are_start_trading_event_args_valid(args_copy) is True
        args_copy[time_parameter_name] = "01-01-2022:13:23"
        assert validator.are_start_trading_event_args_valid(args_copy) is False

    @staticmethod
    @pytest.mark.parametrize("time_parameter_name", ["start_time", "end_time"])
    def test_validate_start_end_time_on_stop_trading(time_parameter_name):
        validator = LiveEventArgsValidator(lambda x, y: None)
        args_copy = deepcopy(correct_args)
        args_copy.pop("capacity_percent")
        args_copy.pop("energy_rate")
        assert validator.are_stop_trading_event_args_valid(args_copy) is True
        args_copy[time_parameter_name] = "01-01-2022:13:23"
        assert validator.are_stop_trading_event_args_valid(args_copy) is False

    @staticmethod
    def test_validate_market_type_on_start_trading():
        validator = LiveEventArgsValidator(lambda x, y: None)
        args_copy = deepcopy(correct_args)
        assert validator.are_start_trading_event_args_valid(args_copy) is True
        args_copy["market_type"] = 12
        assert validator.are_start_trading_event_args_valid(args_copy) is False

    @staticmethod
    def test_validate_market_type_on_stop_trading():
        validator = LiveEventArgsValidator(lambda x, y: None)
        args_copy = deepcopy(correct_args)
        args_copy.pop("capacity_percent")
        args_copy.pop("energy_rate")
        assert validator.are_stop_trading_event_args_valid(args_copy) is True
        args_copy["market_type"] = 12
        assert validator.are_stop_trading_event_args_valid(args_copy) is False
