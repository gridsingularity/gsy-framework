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
from pendulum import DateTime
from d3a_interface.constants_limits import DATE_TIME_UI_FORMAT, DATE_TIME_FORMAT
import time


def convert_datetime_to_str_in_list(in_list, ui_format=False):
    """
    Converts all Datetime elements in a list into strings in DATE_TIME_FORMAT
    """
    out_list = []
    for datetime in in_list:
        if isinstance(datetime, DateTime):
            if not ui_format:
                out_list.append(datetime.format(DATE_TIME_FORMAT))
            else:
                out_list.append(datetime.format(DATE_TIME_UI_FORMAT))
    return out_list


def generate_market_slot_list_from_config(sim_duration, start_date, market_count, slot_length):
    """
    Returns a list of all slot times in Datetime format
    """
    return [
        start_date + (slot_length * i) for i in range(
            (sim_duration + (market_count * slot_length)) //
            slot_length - 1)
        if (slot_length * i) <= sim_duration]


def wait_until_timeout_blocking(functor, timeout=10, polling_period=0.01):
    current_time = 0.0
    while not functor() and current_time < timeout:
        start_time = time.time()
        time.sleep(polling_period)
        current_time += time.time() - start_time
    assert functor()


def key_in_dict_and_not_none(d, key):
    return key in d and d[key] is not None


def key_in_dict_and_not_none_and_negative(d, key):
    return key in d and d[key] is not None and d[key] < 0
