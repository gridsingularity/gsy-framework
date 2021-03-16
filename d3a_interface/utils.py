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
import gc
import pathlib
import sys
import json
import time
import logging
from typing import Dict, List, Callable
from functools import wraps, lru_cache
from collections import OrderedDict
from copy import copy
from threading import Timer
from pkgutil import walk_packages
from redis.exceptions import ConnectionError
from pendulum import DateTime, from_format, from_timestamp, duration, today, datetime
from d3a_interface.constants_limits import DATE_TIME_UI_FORMAT, DATE_TIME_FORMAT, TIME_FORMAT, \
    DATE_TIME_FORMAT_SECONDS, DEFAULT_PRECISION, GlobalConfig, TIME_ZONE, CN_PROFILE_EXPANSION_DAYS


def convert_datetime_to_str_in_list(in_list: List, ui_format: bool = False):
    """
    Converts all Datetime elements in a list into strings in DATE_TIME_FORMAT
    @param in_list: List with datetimes that will be converted to datetime strings
    @param ui_format: Boolean parameter that switches between  DATE_TIME_FORMAT and
                      DATE_TIME_UI_FORMAT
    @return: List with datetime strings
    """
    out_list = []
    for in_datetime in in_list:
        if isinstance(in_datetime, DateTime):
            if not ui_format:
                out_list.append(in_datetime.format(DATE_TIME_FORMAT))
            else:
                out_list.append(in_datetime.format(DATE_TIME_UI_FORMAT))
    return out_list


def generate_market_slot_list_from_config(sim_duration: duration, start_date: DateTime,
                                          market_count: int, slot_length: duration):
    """
    Returns a list of all slot times in Datetime format
    @param sim_duration: Total simulation duration
    @param start_date: Start datetime of the simulation
    @param market_count: Number of future markets
    @param slot_length: Market slot length
    @return: List with market slot datetimes
    """
    return [
        start_date + (slot_length * i) for i in range(
            (sim_duration + (market_count * slot_length)) //
            slot_length - 1)
        if (slot_length * i) <= sim_duration]


def generate_market_slot_list():
    """
    Creates a list with datetimes that correspond to market slots of the simulation.
    No input arguments, required input is only handled by a preconfigured GlobalConfig
    @return: List with market slot datetimes
    """
    start_date = today(tz=TIME_ZONE) \
        if GlobalConfig.IS_CANARY_NETWORK else GlobalConfig.start_date
    time_span = duration(days=CN_PROFILE_EXPANSION_DAYS) \
        if GlobalConfig.IS_CANARY_NETWORK else GlobalConfig.sim_duration
    sim_duration_plus_future_markets = time_span + GlobalConfig.slot_length * \
        (GlobalConfig.market_count - 1)
    market_slot_list = \
        generate_market_slot_list_from_config(sim_duration=sim_duration_plus_future_markets,
                                              start_date=start_date,
                                              market_count=GlobalConfig.market_count,
                                              slot_length=GlobalConfig.slot_length)

    if not getattr(GlobalConfig, 'market_slot_list', []):
        GlobalConfig.market_slot_list = market_slot_list
    return market_slot_list


def find_object_of_same_weekday_and_time(indict: Dict, time_slot: DateTime,
                                         ignore_not_found: bool = False):
    """
    Based on a profile with datetimes that span in one week as keys and some values, finds the
    corresponding value of the same weekday and time. This method is mainly useful for Canary
    Network, during which profiles get recycled every week. Therefore in order to find the
    value of a profile that corresponds to any requested time, the requested time slot is
    mapped on the week that the profile includes, and returns the value of the profile on the
    same weekday and on the same time
    @param indict: profile dict (keys are datetimes, values are arbitrary objects, but usually
                   floats) that contains data for one week that will be used as reference for
                   the requested time_slots
    @param time_slot: DateTime value that represents the requested time slot
    @param ignore_not_found: Boolean parameter that controls whether an error log will be reported
                             if the time_slot cannot be found in the original dict
    @return: Profile value for the requested time slot
    """
    if GlobalConfig.IS_CANARY_NETWORK:
        start_time = list(indict.keys())[0]
        add_days = time_slot.weekday() - start_time.weekday()
        if add_days < 0:
            add_days += 7
        timestamp_key = datetime(year=start_time.year, month=start_time.month, day=start_time.day,
                                 hour=time_slot.hour, minute=time_slot.minute, tz=TIME_ZONE).add(
            days=add_days)

        if timestamp_key in indict:
            return indict[timestamp_key]
        else:
            if not ignore_not_found:
                logging.error(f"Weekday and time not found in dict for {time_slot}")
            return

    else:
        return indict[time_slot]


def wait_until_timeout_blocking(functor: Callable, timeout: int = 10, polling_period: int = 0.01):
    """
    Sleeps until the timeout value, or until functor returns a value that is evaluated to True.
    The operation is blocking/poll based.
    @param functor: Function without arguments that will be called consecutive times expecting
                    to return something that will not be evaluated by 'if not'
    @param timeout: Timeout value after which an assertion will be raised, if the functor does not
                    return the expected value
    @param polling_period: How frequent is the functor evaluated
    @return: None
    """
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


def key_in_dict_and_not_none_and_list_type(d, key):
    return key_in_dict_and_not_none(d, key) and isinstance(d[key], list)


def key_in_dict_and_not_none_and_dict_type(d, key):
    return key_in_dict_and_not_none(d, key) and isinstance(d[key], dict)


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


def datetime_str_to_ui_formatted_datetime_str(input_str):
    return format_datetime(str_to_pendulum_datetime(input_str), ui_format=True)


def ui_str_to_pendulum_datetime(input_str):
    if input_str is None:
        return None
    try:
        pendulum_time = from_format(input_str, DATE_TIME_UI_FORMAT)
    except ValueError:
        raise Exception(f"Format is not '{DATE_TIME_UI_FORMAT}'.")
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


def convert_pendulum_to_str_in_dict(indict, outdict=None, ui_format=False, unix_time=False):
    if outdict is None:
        outdict = {}
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


def convert_str_to_pendulum_in_dict(indict):
    return {str_to_pendulum_datetime(k): v for k, v in indict.items()}


def mkdir_from_str(directory: str, exist_ok=True, parents=True):
    out_dir = pathlib.Path(directory)
    out_dir.mkdir(exist_ok=exist_ok, parents=parents)
    return out_dir


def create_or_update_subdict(indict, key, subdict):
    if key not in indict.keys():
        indict[key] = {}
    indict[key].update(subdict)


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


def check_redis_health(redis_db):
    is_connected = False
    reconnect_needed = False
    while is_connected is False:
        try:
            is_connected = redis_db.ping()
        except ConnectionError:
            logging.debug("Redis not yet available - sleeping")
            time.sleep(0.25)
            reconnect_needed = True
    return reconnect_needed


def get_area_name_uuid_mapping(serialized_scenario, mapping={}):
    if key_in_dict_and_not_none(serialized_scenario, "name") and \
            key_in_dict_and_not_none(serialized_scenario, "uuid"):
        mapping.update({serialized_scenario['name']: serialized_scenario['uuid']})
    if key_in_dict_and_not_none(serialized_scenario, "children"):
        for child in serialized_scenario["children"]:
            new_mapping = get_area_name_uuid_mapping(child, mapping)
            mapping.update(new_mapping)
    return mapping


def get_area_uuid_name_mapping(area_dict, results):
    if key_in_dict_and_not_none(area_dict, "name") and \
            key_in_dict_and_not_none(area_dict, "uuid"):
        results[area_dict["uuid"]] = area_dict["name"]
    if key_in_dict_and_not_none(area_dict, "children"):
        for child in area_dict["children"]:
            results.update(get_area_uuid_name_mapping(child, results))
    return results


def round_floats_for_ui(number):
    return round(number, 3)


def create_subdict_or_update(indict, key, subdict):
    if key in indict:
        indict[key].update(subdict)
    else:
        indict[key] = subdict
    return indict


def add_or_create_key(dict, key, value):
    if key in dict:
        dict[key] += value
    else:
        dict[key] = value
    return dict


def subtract_or_create_key(dict, key, value):
    if key in dict:
        dict[key] -= value
    else:
        dict[key] = 0 - value
    return dict


def make_iaa_name_from_dict(owner):
    return f"IAA {owner['name']}"


def limit_float_precision(number):
    return round(number, DEFAULT_PRECISION)


def if_not_in_list_append(target_list, obj):
    if obj not in target_list:
        target_list.append(obj)


def iterate_over_all_modules(modules_path):
    module_list = []
    for loader, module_name, is_pkg in walk_packages(modules_path):
        if is_pkg:
            loader.find_module(module_name).load_module(module_name)
        else:
            module_list.append(module_name)
    return module_list


def deep_size_of(input_obj):
    """
    Gets the real size of a python object taking into consideration the nested objects
    Note :
    This function works well with data containers (such as lists or dicts)
    However, one thing to take into consideration is that it may return ambiguous result because of
    the fact that an object can be referenced by multiple objects as in the following scenario :

    Given object A declared and referenced object B
    AND   object C referenced object B
    AND   we need to calculate the size of object A to clean memory
    THEN  we will get the size of B returned, giving a false feeling that
        cleaning A will free this amount

    """
    memory_size = sys.getsizeof(input_obj)
    ids = set()
    objects = [input_obj]
    while objects:
        referents_objs = []
        for obj in objects:
            if id(obj) not in ids:
                ids.add(id(obj))
                memory_size += sys.getsizeof(obj)
                referents_objs.append(obj)
        objects = gc.get_referents(*referents_objs)
    return memory_size


def utf8len(s):
    return len(s.encode('utf-8'))


def get_json_dict_memory_allocation_size(json_dict):
    return utf8len(json.dumps(json_dict)) / 1024.


def area_name_from_area_or_iaa_name(name):
    return name[4:] if name[:4] == 'IAA ' else name


def area_bought_from_child(trade: dict, area_name: str, child_names: list):
    return area_name_from_area_or_iaa_name(trade['buyer']) == area_name and \
           area_name_from_area_or_iaa_name(trade['seller']) in child_names


def area_sells_to_child(trade: dict, area_name: str, child_names: list):
    return area_name_from_area_or_iaa_name(trade['seller']) == area_name and \
           area_name_from_area_or_iaa_name(trade['buyer']) in child_names


def convert_W_to_kWh(power_W, slot_length):
    return (slot_length / duration(hours=1)) * power_W / 1000


def convert_W_to_Wh(power_W, slot_length):
    return (slot_length / duration(hours=1)) * power_W


def convert_kW_to_kWh(power_W, slot_length):
    return convert_W_to_Wh(power_W, slot_length)


def return_ordered_dict(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        return OrderedDict(sorted(function(*args, **kwargs).items()))
    return wrapper


def scenario_representation_traversal(sc_repr, parent=None):
    """
        Yields scenario representation in tuple form: ( child, parent )
    """
    children = []
    if type(sc_repr) == dict and "children" in sc_repr:
        children = sc_repr["children"]
    elif hasattr(sc_repr, "children"):
        children = getattr(sc_repr, "children")
    if children is not None:
        for child in children:
            yield from scenario_representation_traversal(child, sc_repr)

    yield sc_repr, parent
