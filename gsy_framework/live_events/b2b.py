from typing import Dict

from gsy_framework.utils import str_to_pendulum_datetime
from gsy_framework.enums import AvailableMarketTypes


class B2BLiveEvents:
    """Live events that support b2b trading."""
    ENABLE_TRADING_EVENT_NAME = "enable_trading"
    DISABLE_TRADING_EVENT_NAME = "disable_trading"
    POST_ORDER_EVENT_NAME = "post_order"
    REMOVE_ORDER_EVENT_NAME = "remove_order"

    @classmethod
    def is_supported_event(cls, event_name) -> bool:
        """Check if the event name is one of the supported live events."""
        return event_name in [
            cls.ENABLE_TRADING_EVENT_NAME, cls.DISABLE_TRADING_EVENT_NAME,
            cls.POST_ORDER_EVENT_NAME, cls.REMOVE_ORDER_EVENT_NAME
        ]


class LiveEventArgsValidator:
    """Validator class for the forward strategy live event arguments."""
    def __init__(self, logger):
        self._logger = logger

    def validate_start_trading_event_args(self, event: Dict) -> bool:
        """Validate the arguments for the start trading event."""
        args = event.get("args")
        accepted_params = ["start_time", "end_time", "market_type",
                           "capacity_percent", "energy_rate"]
        if any(param not in args or not args[param] for param in accepted_params):
            self._logger.error(
                "Parameters start_time, end_time, capacity_percent, energy_rate and market_type "
                "are obligatory for the start trading live events (%s).", event)
            return False

        return (self._validate_market_type(args) and self._validate_start_end_time(args) and
                self._validate_capacity_percent(args) and self._validate_energy_rate(args))

    def validate_stop_trading_event_args(self, event: Dict) -> bool:
        """Valiaate the arguments for the stop trading event."""
        args = event.get("args")
        accepted_params = ["start_time", "end_time", "market_type"]
        if any(param not in args or not args[param] for param in accepted_params):
            self._logger.error(
                "Parameters start_time, end_time and market_type are obligatory "
                "for the stop trading live events (%s).", event)
            return False

        return self._validate_market_type(args) and self._validate_start_end_time(args)

    def _validate_market_type(self, args: Dict) -> bool:
        try:
            AvailableMarketTypes(args["market_type"])
        except ValueError:
            self._logger.error("Cannot deserialize market type parameter (%s).", args)
            return False
        return True

    def _validate_start_end_time(self, args: Dict) -> bool:
        try:
            str_to_pendulum_datetime(args["start_time"])
            str_to_pendulum_datetime(args["end_time"])
        except Exception:
            self._logger.log.error("Cannot deserialize start / end time parameters (%s).", args)
            return False
        return True

    def _validate_capacity_percent(self, args: Dict) -> bool:
        if not 0 <= args["capacity_percent"] <= 100.0:
            self._logger.error(
                "Capacity percent parameter is not in the expected range (%s).", args)
            return False
        return True

    def _validate_energy_rate(self, args: Dict) -> bool:
        if args["energy_rate"] < 0.:
            self._logger.error(
                "Energy rate parameter is negative (%s).", args)
            return False
        return True
