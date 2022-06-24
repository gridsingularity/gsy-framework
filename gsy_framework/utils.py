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
import gc
import json
import logging
import pathlib
import sys
import time
from collections import OrderedDict
from copy import copy
from functools import lru_cache, wraps
from pkgutil import walk_packages
from statistics import mean
from threading import Timer
from typing import Callable, Dict, List
from uuid import UUID

from pendulum import DateTime, datetime, duration, from_format, instance
from redis.exceptions import ConnectionError  # pylint: disable=redefined-builtin

from gsy_framework.constants_limits import (
    DATE_TIME_FORMAT, DATE_TIME_FORMAT_HOURS, DATE_TIME_FORMAT_SECONDS, DATE_TIME_UI_FORMAT,
    DEFAULT_PRECISION, PROFILE_EXPANSION_DAYS, TIME_FORMAT, TIME_FORMAT_HOURS, TIME_FORMAT_SECONDS,
    TIME_ZONE, GlobalConfig)


def execute_function_util(function: callable, function_name: str):
    """Log exceptions raised by the given callable without re-raising them.

    This utility is used to log errors in functions submitted to ThreadPoolExecutor instances.
    """
    try:
        function()
    except Exception as ex:  # pylint: disable=broad-except
        logging.exception("%s raised exception: %s.", function_name, ex)


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


def generate_market_slot_list_from_config(sim_duration: duration, start_timestamp: DateTime,
                                          slot_length: duration, ignore_duration_check=False):
    """
    Returns a list of all slot times in Datetime format.

    Args:
        sim_duration: Total simulation duration
        start_timestamp: Start datetime of the simulation
        slot_length: Market slot length
        ignore_duration_check: Ignores the check if each timestamp is in the simulation duration.
                               Useful for calling the method from context where no config has been
                               set

    Returns: List with market slot datetimes
    """
    return [
        start_timestamp + (slot_length * i) for i in range(
            (sim_duration + slot_length) //
            slot_length - 1)
        if (ignore_duration_check or
            is_time_slot_in_simulation_duration(start_timestamp + (slot_length * i)))]


def generate_market_slot_list(start_timestamp=None):
    """
    Creates a list with datetimes that correspond to market slots of the simulation.
    No input arguments, required input is only handled by a preconfigured GlobalConfig
    @return: List with market slot datetimes
    """
    time_span = duration(days=PROFILE_EXPANSION_DAYS)\
        if GlobalConfig.IS_CANARY_NETWORK \
        else min(GlobalConfig.sim_duration, duration(days=PROFILE_EXPANSION_DAYS))
    time_span += duration(hours=GlobalConfig.FUTURE_MARKET_DURATION_HOURS)
    market_slot_list = \
        generate_market_slot_list_from_config(sim_duration=time_span,
                                              start_timestamp=start_timestamp
                                              if start_timestamp else GlobalConfig.start_date,
                                              slot_length=GlobalConfig.slot_length)

    if not getattr(GlobalConfig, "market_slot_list", []):
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
    start_time = list(indict.keys())[0]
    add_days = time_slot.weekday() - start_time.weekday()
    if add_days < 0:
        add_days += 7
    timestamp_key = datetime(
        year=start_time.year, month=start_time.month, day=start_time.day, hour=time_slot.hour,
        minute=time_slot.minute, tz=TIME_ZONE).add(days=add_days)

    if timestamp_key in indict:
        return indict[timestamp_key]

    if not ignore_not_found:
        logging.error("Weekday and time not found in dict for %s", time_slot)

    return None


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


def key_in_dict_and_not_none(dictionary, key):
    """Check if the given dictionary contains the specified key."""
    return key in dictionary and dictionary[key] is not None


def key_in_dict_and_not_none_and_not_str_type(dictionary, key):
    """Check if the given dictionary contains the specified key."""
    return key_in_dict_and_not_none(dictionary, key) and not isinstance(dictionary[key], str)


def key_in_dict_and_not_none_and_greater_than_zero(dictionary, key):
    """Check if the given dictionary contains the specified key and it is greater than 0."""
    return key in dictionary and dictionary[key] is not None and dictionary[key] > 0


def key_in_dict_and_not_none_and_negative(dictionary, key):
    """Check if the given dictionary contains the specified key and it is both not None and < 0."""
    return key in dictionary and dictionary[key] is not None and dictionary[key] < 0


def str_to_pendulum_datetime(input_str: str) -> DateTime:
    """Convert a string to pendulum datetime format."""
    if input_str is None:
        return None

    supported_formats = [TIME_FORMAT, DATE_TIME_FORMAT, TIME_FORMAT_HOURS,
                         DATE_TIME_FORMAT_SECONDS, TIME_FORMAT_SECONDS, DATE_TIME_FORMAT_HOURS]

    for datetime_format in supported_formats:
        try:
            return from_format(input_str, datetime_format)
        except ValueError:
            continue
    raise Exception(f"Format of {input_str} is not one of {supported_formats}")


def datetime_str_to_ui_formatted_datetime_str(input_str: str) -> str:
    """Format a string using the format required by the UI."""
    return format_datetime(str_to_pendulum_datetime(input_str), ui_format=True)


def ui_str_to_pendulum_datetime(input_str) -> DateTime:
    """Convert a string with UI format into a pendulum.datetime.Datetime object."""
    if input_str is None:
        return None
    try:
        pendulum_time = from_format(input_str, DATE_TIME_UI_FORMAT)
    except ValueError as ex:
        raise Exception(f'Format is not "{DATE_TIME_UI_FORMAT}".') from ex
    return pendulum_time


@lru_cache(maxsize=100, typed=False)
def format_datetime(datetime_object, ui_format=False, unix_time=False) -> str:
    """Convert a datetime object into a string.

    The format of the string can be one of the following: default datetime, UI format or unix time.
    """
    if unix_time:
        return datetime_object.timestamp()
    if ui_format:
        return datetime_object.format(DATE_TIME_UI_FORMAT)

    return datetime_object.format(DATE_TIME_FORMAT)


def datetime_to_string_incl_seconds(date_time: DateTime) -> str:
    """Convert a datetime object into a string that includes seconds."""
    if not date_time:
        return ""
    return date_time.format(DATE_TIME_FORMAT_SECONDS)


def convert_pendulum_to_str_in_dict(indict, outdict=None, ui_format=False, unix_time=False):
    """Convert occurrences of pendulum DateTime objects within the given dictionary into strings.

    The strings format can be one of the following: default datetime, UI format or unix time.
    """
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
    """Convert datetime strings within the given dictionary into pendulum DateTime objects."""
    return {str_to_pendulum_datetime(k): v for k, v in indict.items()}


def mkdir_from_str(directory: str, exist_ok=True, parents=True) -> str:
    """Create a directory using the provided path."""
    out_dir = pathlib.Path(directory)
    out_dir.mkdir(exist_ok=exist_ok, parents=parents)
    return out_dir


def create_or_update_subdict(indict: Dict, key, subdict: Dict):
    """Update a dictionary with the contents of a specific key from another dictionary.

    Args:
        indict: the dictionary that will be updated.
        key: the key to be moved into `indict` together with its value.
        subdict: the original dictionary whose content will be used to updated the `indict`.
    """
    if key not in indict.keys():
        indict[key] = {}
    indict[key].update(subdict)


def create_subdict_or_update(indict, key, subdict):
    """Update a dictionary with the contents of a specific key from another dictionary."""
    if key in indict:
        indict[key].update(subdict)
    else:
        indict[key] = subdict
    return indict


class RepeatingTimer(Timer):
    """Threading timer that repeats the execution of a function at predefined intervals."""
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


def check_redis_health(redis_db):
    """Check the status of the Redis connectivity."""
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


# pylint: disable=dangerous-default-value
def get_area_name_uuid_mapping(serialized_scenario, mapping={}):
    """Return the mapping between area names and their UUIDs."""
    if key_in_dict_and_not_none(serialized_scenario, "name") and \
            key_in_dict_and_not_none(serialized_scenario, "uuid"):
        mapping.update({serialized_scenario["name"]: serialized_scenario["uuid"]})
    if key_in_dict_and_not_none(serialized_scenario, "children"):
        for child in serialized_scenario["children"]:
            new_mapping = get_area_name_uuid_mapping(child, mapping)
            mapping.update(new_mapping)
    return mapping


def get_area_uuid_name_mapping(area_dict, results):
    """Return the mapping between area UUIDs and their names."""
    if key_in_dict_and_not_none(area_dict, "name") and key_in_dict_and_not_none(area_dict, "uuid"):
        results[area_dict["uuid"]] = area_dict["name"]
    if key_in_dict_and_not_none(area_dict, "children"):
        for child in area_dict["children"]:
            results.update(get_area_uuid_name_mapping(child, results))
    return results


def round_floats_for_ui(number):
    """Round the given number using the scale required by the UI."""
    return round(number, 3)


def round_prices_to_cents(number):
    """Round the given number using 2-digits scale (to represent cents)."""
    return round(number, 2)


def add_or_create_key(dictionary, key, value):
    """Increase the amount at the given key by the provided value."""
    if key in dictionary:
        dictionary[key] += value
    else:
        dictionary[key] = value
    return dictionary


def subtract_or_create_key(dictionary, key, value):
    """Decrease the amount at the given key by the provided value."""
    if key in dictionary:
        dictionary[key] -= value
    else:
        dictionary[key] = 0 - value
    return dictionary


def limit_float_precision(number):
    """Round a number to the default precision after the comma."""
    return round(number, DEFAULT_PRECISION)


def if_not_in_list_append(target_list, obj):
    """Append element to the list if it's not already part of it."""
    if obj not in target_list:
        target_list.append(obj)


def iterate_over_all_modules(modules_path):
    """Return all modules in the given path."""
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


def utf8len(string: str) -> int:
    """Return the length of a string encoded in UTF-8 format."""
    return len(string.encode("utf-8"))


def get_json_dict_memory_allocation_size(json_dict: Dict):
    """Return the memory allocation of the provided dictionary."""
    return utf8len(json.dumps(json_dict)) / 1024.


def area_name_from_area_or_ma_name(name: str) -> str:
    """Retrieve the name of the area.

    The input can be either the area name itself or the name of the market agent of the area.
    """
    return name[3:] if name[:3] == "MA " else name


def area_bought_from_child(trade: dict, area_name: str, child_names: list):
    """Check if the area with the given name bought energy from one of its children."""
    return (
        area_name_from_area_or_ma_name(trade["buyer"]) == area_name
        and area_name_from_area_or_ma_name(trade["seller"]) in child_names)


def area_sells_to_child(trade: dict, area_name: str, child_names: list):
    """Check if the area with the given name sold energy to one of its children."""
    return (
        area_name_from_area_or_ma_name(trade["seller"]) == area_name
        and area_name_from_area_or_ma_name(trade["buyer"]) in child_names)


# pylint: disable=invalid-name
def convert_W_to_kWh(power_W, slot_length):
    """Convert W power into energy in kWh (based on the duration of the market slot)."""
    return (slot_length / duration(hours=1)) * power_W / 1000


# pylint: disable=invalid-name
def convert_W_to_Wh(power_W, slot_length):
    """Convert W power into energy in Wh (based on the duration of the market slot)."""
    return (slot_length / duration(hours=1)) * power_W


# pylint: disable=invalid-name
def convert_kW_to_kWh(power_W, slot_length):
    """Convert kW power into kWh energy (based on the duration of the market slot)."""
    return convert_W_to_Wh(power_W, slot_length)


def return_ordered_dict(function):
    """Decorator to convert the dictionary returned by the wrapped function into an OrderedDict."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        return OrderedDict(sorted(function(*args, **kwargs).items()))
    return wrapper


def scenario_representation_traversal(sc_repr, parent=None):
    """Yield scenario representation in tuple form: (child, parent)."""
    children = []
    if isinstance(sc_repr, dict) and "children" in sc_repr:
        children = sc_repr["children"]
    elif hasattr(sc_repr, "children"):
        children = getattr(sc_repr, "children")
    if children is not None:
        for child in children:
            yield from scenario_representation_traversal(child, sc_repr)

    yield sc_repr, parent


class HomeRepresentationUtils:
    """Class to calculate the stats of a home market."""
    @staticmethod
    def _is_home(representation):
        home_devices = ["PV", "Storage", "Load", "MarketMaker"]
        return all("type" in c and c["type"] in home_devices
                   for c in representation["children"])

    @classmethod
    def is_home_area(cls, representation: Dict) -> bool:
        """Check if the representation is a market."""
        is_market_area = (
            not key_in_dict_and_not_none(representation, "type")
            or representation["type"] == "Area")
        has_home_assets = (
            key_in_dict_and_not_none(representation, "children")
            and representation["children"]
            and cls._is_home(representation))

        return is_market_area and has_home_assets

    @classmethod
    def calculate_home_area_stats_from_repr_dict(cls, representation: Dict):
        """Compute the stats of the home from its representation."""
        devices_per_home = [
            len(area["children"])
            for area, _ in scenario_representation_traversal(representation)
            if cls.is_home_area(area)
        ]
        return len(devices_per_home), mean(devices_per_home) if devices_per_home else None


def sort_list_of_dicts_by_attribute(input_list: List[Dict], attribute: str, reverse_order=False):
    """Sorts a list of dicts by a given attribute.

    Args:
        input_list: List[Dict]
        attribute: attribute to sort against
        reverse_order: if True, the returned list will be sorted in descending order

    Returns: List[Dict]

    """
    if reverse_order:
        # Sorted bids in descending order
        return list(
            reversed(
                sorted(input_list, key=lambda obj: obj.get(attribute))))

    # Sorted bids in ascending order
    return sorted(input_list, key=lambda obj: obj.get(attribute))


def convert_datetime_to_ui_str_format(data_time):
    """Convert a datetime object into the format required by the UI."""
    return instance(data_time).format(DATE_TIME_UI_FORMAT)


def is_time_slot_in_simulation_duration(
        time_slot: DateTime, config: "GlobalConfig" = None) -> bool:
    """
        Check whether a specific timeslot is inside the range of the simulation duration.

    Args:
        time_slot: Timeslot that is checked if it is in the simulation duration
        config: Optional configuration settings object that is used for the start / end date
                parameters. In case it is not provided, GlobalConfig object is used instead

    Returns: True if the timeslot is in the simulation duration, false otherwise
    """
    if config is None:
        start_date = GlobalConfig.start_date
        end_date = GlobalConfig.start_date + GlobalConfig.sim_duration
    else:
        start_date = config.start_date
        end_date = config.end_date
    return start_date <= time_slot < end_date or GlobalConfig.IS_CANARY_NETWORK


def is_valid_uuid(uuid: str) -> bool:
    """Return if the provided string is a valid uuid."""
    try:
        UUID(str(uuid), version=4)
    except ValueError:
        return False

    return True
