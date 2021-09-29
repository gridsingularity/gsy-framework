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
import csv
import os
import ast
from typing import Any
from enum import Enum
from pendulum import duration, from_format, from_timestamp, today, DateTime
from typing import Dict

from d3a_interface.constants_limits import TIME_FORMAT, DATE_TIME_FORMAT, GlobalConfig, \
    DATE_TIME_FORMAT_SECONDS, TIME_ZONE
from d3a_interface.utils import convert_kW_to_kWh, return_ordered_dict, \
    generate_market_slot_list, find_object_of_same_weekday_and_time
from d3a_interface.exceptions import D3AReadProfileException

"""
Exposes mixins that can be used from strategy classes.
"""


DATE_TIME_FORMAT_SPACED = f"YYYY-MM-DD HH:mm:ss"


class InputProfileTypes(Enum):
    IDENTITY = 1
    POWER = 2


def _str_to_datetime(time_str, time_format) -> DateTime:
    """
    Converts time_str into a pendulum (DateTime) object that either takes the global start date or
    the provided one, dependant on the time_format
    :return: DateTime
    """
    time = from_format(time_str, time_format, tz=TIME_ZONE)
    if time_format in [DATE_TIME_FORMAT, DATE_TIME_FORMAT_SECONDS, DATE_TIME_FORMAT_SPACED]:
        return time
    elif time_format == TIME_FORMAT:
        return GlobalConfig.start_date.add(
            hours=time.hour, minutes=time.minute, seconds=time.second)
    else:
        raise D3AReadProfileException("Provided time_format invalid.")


def default_profile_dict(val=None, current_timestamp=None) -> Dict[DateTime, int]:
    """
    Returns dictionary with default values for all market slots.
    :param val: Default value
    """
    if val is None:
        val = 0
    return {time_slot: val
            for time_slot in
            generate_market_slot_list(start_timestamp=current_timestamp)}


def is_number(number):
    try:
        float(number)
        return True
    except ValueError:
        return False


def _remove_header(profile_dict: Dict) -> Dict:
    """
    Checks profile for header entries and removes these
    Header entries have values that are not representations of numbers
    """
    out_dict = {}
    for k, v in profile_dict.items():
        if is_number(v):
            out_dict[k] = v
    return out_dict


def _eval_single_format(time_dict, time_format):
    try:
        [from_format(str(ti), time_format) for ti in time_dict.keys()]
        return time_format
    except ValueError:
        return None


def _eval_time_format(time_dict: Dict) -> str:
    """
    Evaluates which time format the provided dictionary has, also checks if the time-format is
    consistent for each time_slot
    :return: TIME_FORMAT or DATE_TIME_FORMAT or DATE_TIME_FORMAT_SECONDS
    """

    for time_format in [TIME_FORMAT, DATE_TIME_FORMAT, DATE_TIME_FORMAT_SECONDS,
                        DATE_TIME_FORMAT_SPACED]:
        if _eval_single_format(time_dict, time_format):
            return time_format

    raise D3AReadProfileException(
        f"Format of time-stamp is not one of ('{TIME_FORMAT}', "
        f"'{DATE_TIME_FORMAT}', '{DATE_TIME_FORMAT_SECONDS}')")


def _readCSV(path: str) -> Dict:
    """
    Read a 2-column csv profile file. First column is the time, second column
    is the value (power, energy, rate, ...)
    :param path: path to csv file
    :return: Dict[DateTime, value]
    """
    profile_data = {}
    with open(path) as csv_file:
        csv_rows = csv.reader(csv_file)
        for row in csv_rows:
            if len(row) == 0:
                raise D3AReadProfileException(
                    f"There must not be an empty line in the profile file {path}")
            if len(row) != 2:
                row = row[0].split(";")
            try:
                profile_data[row[0]] = float(row[1])
            except ValueError:
                pass
    time_format = _eval_time_format(profile_data)
    return dict((_str_to_datetime(time_str, time_format), value)
                for time_str, value in profile_data.items())


def _interpolate_profile_values_to_slot(profile_data_W, slot_length):
    input_time_list = list(profile_data_W.keys())

    # add one market slot in order to have another data point for integration
    additional_time_stamp = input_time_list[-1] + slot_length
    profile_data_W[additional_time_stamp] = profile_data_W[input_time_list[-1]]
    input_time_list.append(additional_time_stamp)

    input_power_list_W = [float(dp) for dp in profile_data_W.values()]

    time0 = from_timestamp(0)
    input_time_seconds_list = [(ti - time0).in_seconds()
                               for ti in input_time_list]

    slot_time_list = [i for i in range(input_time_seconds_list[0], input_time_seconds_list[-1],
                                       slot_length.in_seconds())]

    second_power_list_W = [
        input_power_list_W[index - 1]
        for index, seconds in enumerate(input_time_seconds_list)
        for _ in range(seconds - input_time_seconds_list[index - 1])
    ]

    avg_power_kW = []
    for index, slot in enumerate(slot_time_list):
        first_index = index * slot_length.in_seconds()
        if first_index <= len(second_power_list_W):
            avg_power_kW.append(second_power_list_W[first_index] / 1000.)

    return avg_power_kW, slot_time_list


def _calculate_energy_from_power_profile(profile_data_W: Dict[DateTime, float],
                                         slot_length: duration) -> Dict[DateTime, float]:
    """
    Calculates energy from power profile. Does not use numpy, calculates avg power for each
    market slot and based on that calculates energy.
    :param profile_data_W: Power profile in W
    :param slot_length: slot length duration
    :return: a mapping from time to energy values in kWh
    """

    avg_power_kW, slot_time_list = _interpolate_profile_values_to_slot(profile_data_W, slot_length)
    slot_energy_kWh = list(map(lambda x: convert_kW_to_kWh(x, slot_length), avg_power_kW))

    return {from_timestamp(slot_time_list[ii]): energy
            for ii, energy in enumerate(slot_energy_kWh)
            }


def _fill_gaps_in_profile(input_profile: Dict = None, out_profile: Dict = None) -> Dict:
    """
    Fills time steps, where no value is provided, with the value value of the
    last available time step.
    :param input_profile: Dict[Datetime: float, int, tuple]
    :param out_profile: dict with the same format as the input_profile that can be used
                        to provide a default zero-value profile dict with the expected timestamps
                        that need to be populated in the profile
    :return: continuous profile Dict[Datetime: float, int, tuple]
    """

    if isinstance(list(input_profile.values())[0], tuple):
        current_val = (0, 0)
    else:
        current_val = 0

    for time in out_profile.keys():
        if GlobalConfig.IS_CANARY_NETWORK:
            temp_val = find_object_of_same_weekday_and_time(input_profile, time,
                                                            ignore_not_found=True)
            if temp_val is not None:
                current_val = temp_val
        else:
            if time in input_profile:
                current_val = input_profile[time]
        out_profile[time] = current_val

    return out_profile


def _read_from_different_sources_todict(
        input_profile: Any, current_timestamp: DateTime = None) -> Dict[DateTime, float]:
    """
    Reads arbitrary profile.
    Handles csv, dict and string input.
    :param input_profile:Can be either a csv file path,
    or a dict with hourly data (Dict[int, float])
    or a dict with arbitrary time data (Dict[str, float])
    or a string containing a serialized dict of the aforementioned structure
    :return:
    """

    if os.path.isfile(str(input_profile)):
        # input is csv file
        profile = _readCSV(input_profile)

    elif isinstance(input_profile, dict) or isinstance(input_profile, str):
        # input is profile

        if isinstance(input_profile, str):
            # input in JSON formatting
            profile = ast.literal_eval(input_profile.encode('utf-8').decode("utf-8-sig"))
            # Remove filename entry to support d3a-web profiles
            profile.pop("filename", None)
            profile = _remove_header(profile)
            time_format = _eval_time_format(profile)
            profile = {_str_to_datetime(key, time_format): val
                       for key, val in profile.items()}
        elif isinstance(list(input_profile.keys())[0], DateTime):
            return input_profile

        elif isinstance(list(input_profile.keys())[0], str):
            # input is dict with string keys that are properly formatted time stamps
            input_profile = _remove_header(input_profile)
            # Remove filename from profile
            input_profile.pop("filename", None)
            time_format = _eval_time_format(input_profile)
            profile = {_str_to_datetime(key, time_format): val
                       for key, val in input_profile.items()}

        elif isinstance(list(input_profile.keys())[0], int) or \
                isinstance(list(input_profile.keys())[0], float):
            # input is hourly profile

            profile = dict(
                (today(tz=TIME_ZONE).add(hours=hour), val)
                for hour, val in input_profile.items()
            )

        else:
            raise D3AReadProfileException(
                "Unsupported input type : " + str(list(input_profile.keys())[0]))

    elif isinstance(input_profile, int) or \
            isinstance(input_profile, float) or \
            isinstance(input_profile, tuple):
        # input is single value
        profile = default_profile_dict(val=input_profile, current_timestamp=current_timestamp)

    else:
        raise D3AReadProfileException(
            f"Unsupported input type: {str(input_profile)}")

    return profile


def time_str(hour, minute):
    return f"{hour:02}:{minute:02}"


def copy_profile_to_multiple_days(in_profile):
    daytime_dict = dict((time_str(time.hour, time.minute), time) for time in in_profile.keys())
    out_profile = {}
    for slot_time in generate_market_slot_list():
        if slot_time not in out_profile.keys():
            time_key = time_str(slot_time.hour, slot_time.minute)
            if time_key in daytime_dict:
                out_profile[slot_time] = in_profile[daytime_dict[time_key]]
    return out_profile


@return_ordered_dict
def read_arbitrary_profile(profile_type: InputProfileTypes,
                           input_profile,
                           current_timestamp: DateTime = None) -> Dict[DateTime, float]:
    """
    Reads arbitrary profile.
    Handles csv, dict and string input.
    Fills gaps in the profile.
    :param profile_type: Can be either rate or power
    :param input_profile: Can be either a csv file path,
    or a dict with hourly data (Dict[int, float])
    or a dict with arbitrary time data (Dict[str, float])
    or a string containing a serialized dict of the aforementioned structure
    :param current_timestamp:
    :return: a mapping from time to profile values
    """

    profile = _read_from_different_sources_todict(input_profile,
                                                  current_timestamp=current_timestamp)
    profile_time_list = list(profile.keys())
    profile_duration = profile_time_list[-1] - profile_time_list[0]
    if GlobalConfig.sim_duration > duration(days=1) >= profile_duration or \
            GlobalConfig.IS_CANARY_NETWORK:
        profile = copy_profile_to_multiple_days(profile)
    if profile is not None:

        zero_value_slot_profile = default_profile_dict(current_timestamp=current_timestamp)
        filled_profile = _fill_gaps_in_profile(profile, zero_value_slot_profile)

        if profile_type == InputProfileTypes.POWER:
            return _calculate_energy_from_power_profile(filled_profile, GlobalConfig.slot_length)
        else:
            return filled_profile


def _generate_slot_based_zero_values_dict_from_profile(profile, slot_length_mins=15):
    profile_time_list = list(profile.keys())
    end_time = profile_time_list[-1]
    start_time = profile_time_list[0]

    slot_length_seconds = slot_length_mins * 60

    offset_seconds = start_time.timestamp() % slot_length_seconds
    start_datetime = from_timestamp(start_time.timestamp() - offset_seconds)

    profile_duration = end_time - start_datetime
    return {
        start_datetime + duration(minutes=slot_length_mins*i): 0.0
        for i in range((int(profile_duration.total_minutes()) // slot_length_mins)+1)
    }


def read_profile_without_config(input_profile: Dict, slot_length_mins=15) -> Dict[DateTime, float]:
    profile = _read_from_different_sources_todict(input_profile)
    if profile is not None:
        slot_based_profile = _generate_slot_based_zero_values_dict_from_profile(
            profile, slot_length_mins
        )
        filled_profile = _fill_gaps_in_profile(profile, slot_based_profile)
        profile_values, slots = _interpolate_profile_values_to_slot(
            filled_profile, duration(minutes=slot_length_mins)
        )
        return {
            from_timestamp(slots[ii]): energy
            for ii, energy in enumerate(profile_values)
        }
    else:
        raise D3AReadProfileException(
            f"Profile file cannot be read successfully. Please reconfigure the file path.")


def read_and_convert_identity_profile_to_float(profile, current_timestamp: DateTime = None):
    parsed_profile = ast.literal_eval(str(profile))
    generated_profile = read_arbitrary_profile(InputProfileTypes.IDENTITY, parsed_profile,
                                               current_timestamp=current_timestamp)
    return {k: float(v) for k, v in generated_profile.items()}


def convert_identity_profile_to_float(profile, current_timestamp: DateTime = None):
    return {k: float(v) for k, v in profile.items()}
