from unittest.mock import MagicMock

from tabulate import tabulate

import d3a_interface
from d3a_interface.client_connections.utils import (
    get_slot_completion_percentage_int_from_message, log_market_progression)


def test_get_slot_completion_percentage_int_from_message():
    message = {"slot_completion": "92%"}
    assert get_slot_completion_percentage_int_from_message(message) == 92

    message = {}
    assert get_slot_completion_percentage_int_from_message(message) is None


def test_log_market_progression(caplog):
    message = {"event": "finish"}
    d3a_interface.client_connections.utils.logging.info = MagicMock()
    log_market_progression(message)
    assert d3a_interface.client_connections.utils.logging.info.call_count == 0

    message = {"event": "market", "market_slot": 2, "start_time": 1, "duration_min": 10,
               "slot_completion": "12%"}
    headers = ["event", "start_time", "duration_min", "slot_completion", "market_slot"]
    table_data = ["market", 1, 10, 12, 2]
    log_market_progression(message)
    assert d3a_interface.client_connections.utils.logging.info.called_once_with(
        f"\n\n{tabulate([table_data, ], headers=headers, tablefmt='fancy_grid')}\n\n"
    )
    message["slot_completion"] = "9%"
    log_market_progression(message)
    assert d3a_interface.client_connections.utils.logging.info.called_once()
