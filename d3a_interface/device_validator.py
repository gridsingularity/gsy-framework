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

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException
from d3a_interface.utils import key_in_dict_and_not_none, key_in_dict_and_not_none_and_not_str_type
from d3a_interface.validators import utils
from d3a_interface.validators.cep_validator import validate_commercial_producer

CepSettings = ConstSettings.CommercialProducerSettings


def validate_market_maker(**kwargs):
    utils.validate_energy_rate(**kwargs)
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
            utils.validate_range_limit(CepSettings.MAX_POWER_KW_LIMIT.min,
                                 kwargs["max_available_power_kW"],
                                 CepSettings.MAX_POWER_KW_LIMIT.max,
                                 error_message)
        elif isinstance(kwargs["max_available_power_kW"], dict):
            error_message = \
                {"misconfiguration": [f"max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            for date, value in kwargs["max_available_power_kW"].items():
                utils.validate_range_limit(CepSettings.MAX_POWER_KW_LIMIT.min, value,
                                     CepSettings.MAX_POWER_KW_LIMIT.max, error_message)
        else:
            raise D3ADeviceException({"misconfiguration": [f"max_available_power_kW has an "
                                                           f"invalid type. "]})

    validate_commercial_producer(**kwargs)
