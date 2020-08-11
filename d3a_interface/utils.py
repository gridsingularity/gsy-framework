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

import pathlib
import os
import logging
import time

from redis.exceptions import ConnectionError
from urllib.parse import urlparse
from redis import StrictRedis
from pendulum import DateTime, from_format, from_timestamp
from functools import lru_cache
from copy import copy
from threading import Timer
from d3a_interface.constants_limits import DATE_TIME_UI_FORMAT, DATE_TIME_FORMAT, TIME_FORMAT, \
    DATE_TIME_FORMAT_SECONDS

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost')


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


def key_in_dict_and_not_none_and_not_str_type(d, key):
    return key_in_dict_and_not_none(d, key) and not isinstance(d[key], str)


def key_in_dict_and_not_none_and_greater_than_zero(d, key):
    return key in d and d[key] is not None and d[key] > 0


def key_in_dict_and_not_none_and_negative(d, key):
    return key in d and d[key] is not None and d[key] < 0


def str_to_pendulum_datetime(input_str):
    if input_str is None:
        return None
    try:
        pendulum_time = from_format(input_str, TIME_FORMAT)
    except ValueError:
        try:
            pendulum_time = from_format(input_str, DATE_TIME_FORMAT)
        except ValueError:
            raise Exception(f"Format is not one of ('{TIME_FORMAT}', '{DATE_TIME_FORMAT}')")
    return pendulum_time


def unix_time_to_str(unix_time, out_format):
    return from_timestamp(unix_time).format(out_format)


@lru_cache(maxsize=100, typed=False)
def format_datetime(datetime, ui_format=False, unix_time=False):
    if unix_time:
        return datetime.timestamp()
    elif ui_format:
        return datetime.format(DATE_TIME_UI_FORMAT)
    else:
        return datetime.format(DATE_TIME_FORMAT)


def datetime_to_string_incl_seconds(datetime):
    return datetime.format(DATE_TIME_FORMAT_SECONDS)


def convert_pendulum_to_str_in_dict(indict, outdict, ui_format=False, unix_time=False):
    for key, value in indict.items():
        if isinstance(key, DateTime):
            outdict[format_datetime(key, ui_format, unix_time)] = indict[key]
        elif isinstance(value, DateTime):
            outdict[key] = format_datetime(value, ui_format, unix_time)
        elif isinstance(value, list):
            outdict[key] = [convert_pendulum_to_str_in_dict(element, {}, ui_format, unix_time)
                            for element in indict[key]]
        elif isinstance(value, dict):
            outdict[key] = {}
            convert_pendulum_to_str_in_dict(indict[key], outdict[key], ui_format, unix_time)
        else:
            outdict[key] = copy(indict[key])
    return outdict


def mkdir_from_str(directory: str, exist_ok=True, parents=True):
    out_dir = pathlib.Path(directory)
    out_dir.mkdir(exist_ok=exist_ok, parents=parents)
    return out_dir


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.finished.wait(self.interval)
            self.function(*self.args, **self.kwargs)


def check_and_wait_for_redis():
    redis_host = urlparse(REDIS_URL).netloc
    info = None
    while not info:
        try:
            info = StrictRedis(redis_host).info()
            logging.debug("REDIS IS ALIVE")
        except ConnectionError:
            logging.error("Redis not yet available - sleeping")
            time.sleep(5)
    return info.get('pubsub_channels', 0)
