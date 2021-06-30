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
import ast

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException
from d3a_interface.utils import key_in_dict_and_not_none, key_in_dict_and_not_none_and_not_str_type
from d3a_interface.validators.utils import validate_range_limit

CepSettings = ConstSettings.CommercialProducerSettings


def _validate_rate(energy_rate):
    error_message = \
        {"misconfiguration": [f"energy_rate should be in between "
                              f"{CepSettings.ENERGY_RATE_LIMIT.min} & "
                              f"{CepSettings.ENERGY_RATE_LIMIT.max}."]}
    validate_range_limit(CepSettings.ENERGY_RATE_LIMIT.min, energy_rate,
                         CepSettings.ENERGY_RATE_LIMIT.max, error_message)


def _validate_rate_profile(energy_rate_profile):
    for date, value in energy_rate_profile.items():
        value = float(value) if type(value) == str else value
        error_message = \
            {"misconfiguration": [f"energy_rate should at time: {date} be in between "
                                  f"{CepSettings.ENERGY_RATE_LIMIT.min} & "
                                  f"{CepSettings.ENERGY_RATE_LIMIT.max}."]}
        validate_range_limit(CepSettings.ENERGY_RATE_LIMIT.min, value,
                             CepSettings.ENERGY_RATE_LIMIT.max, error_message)


def validate_energy_rate(**kwargs):
    if "energy_rate" in kwargs and kwargs["energy_rate"] is not None:
        if isinstance(kwargs["energy_rate"], (float, int)):
            _validate_rate(kwargs["energy_rate"])
        elif isinstance(kwargs["energy_rate"], str):
            _validate_rate_profile(ast.literal_eval(kwargs["energy_rate"]))
        elif isinstance(kwargs["energy_rate"], dict):
            _validate_rate_profile(kwargs["energy_rate"])
        else:
            raise D3ADeviceException({"misconfiguration": [f"energy_rate has an invalid type."]})


def validate_commercial_producer(**kwargs):
    validate_energy_rate(**kwargs)


def validate_market_maker(**kwargs):
    validate_energy_rate(**kwargs)
    if "energy_rate_profile" in kwargs and kwargs["energy_rate_profile"] is not None and \
            ("energy_rate_profile_uuid" not in kwargs or
             kwargs["energy_rate_profile_uuid"] is None):
        raise D3ADeviceException(
            {"misconfiguration": [f"energy_rate_profile must have a uuid."]})
    if "grid_connected" in kwargs and kwargs["grid_connected"] is not None and \
            not isinstance(kwargs["grid_connected"], bool):
        raise D3ADeviceException(
            {"misconfiguration": [f"grid_connected must be a boolean value."]})


def validate_infinite_bus(**kwargs):
    validate_commercial_producer(**kwargs)
    if "energy_rate_profile" in kwargs and kwargs["energy_rate_profile"] is not None and \
            ("energy_rate_profile_uuid" not in kwargs or
             kwargs["energy_rate_profile_uuid"] is None):
        raise D3ADeviceException(
            {"misconfiguration": [f"energy_rate_profile must have a uuid."]})
    if key_in_dict_and_not_none_and_not_str_type(kwargs, "energy_rate_profile_uuid"):
        raise D3ADeviceException(
            {"misconfiguration": [f"energy_rate_profile_uuid must have a string type."]})

    if key_in_dict_and_not_none(kwargs, "energy_buy_rate"):
        _validate_rate(kwargs['energy_buy_rate'])
    if key_in_dict_and_not_none(kwargs, "buying_rate_profile") and \
            ("buying_rate_profile_uuid" not in kwargs or
             kwargs["buying_rate_profile_uuid"] is None):
        raise D3ADeviceException(
            {"misconfiguration": [f"buying_rate_profile must have a uuid."]})
    if key_in_dict_and_not_none_and_not_str_type(kwargs, "buying_rate_profile_uuid"):
        raise D3ADeviceException(
            {"misconfiguration": [f"buying_rate_profile_uuid must have a string type."]})


def validate_finite_diesel_generator(**kwargs):
    if "max_available_power_kW" in kwargs and kwargs["max_available_power_kW"] is not None:
        if isinstance(kwargs["max_available_power_kW"], (int, float)):
            error_message = \
                {"misconfiguration": [f"max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            validate_range_limit(CepSettings.MAX_POWER_KW_LIMIT.min,
                                 kwargs["max_available_power_kW"],
                                 CepSettings.MAX_POWER_KW_LIMIT.max,
                                 error_message)
        elif isinstance(kwargs["max_available_power_kW"], dict):
            error_message = \
                {"misconfiguration": [f"max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            for date, value in kwargs["max_available_power_kW"].items():
                validate_range_limit(CepSettings.MAX_POWER_KW_LIMIT.min, value,
                                     CepSettings.MAX_POWER_KW_LIMIT.max, error_message)
        else:
            raise D3ADeviceException({"misconfiguration": [f"max_available_power_kW has an "
                                                           f"invalid type. "]})

    validate_commercial_producer(**kwargs)
