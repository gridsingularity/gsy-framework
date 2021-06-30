"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If
not, see <http://www.gnu.org/licenses/>.
"""
from d3a_interface.exceptions import D3ADeviceException
from d3a_interface.utils import key_in_dict_and_not_none, key_in_dict_and_not_none_and_not_str_type
from d3a_interface.validators import utils
from d3a_interface.validators.cep_validator import validate_commercial_producer


def validate_infinite_bus(**kwargs):
    validate_commercial_producer(**kwargs)
    if "energy_rate_profile" in kwargs and kwargs["energy_rate_profile"] is not None and \
            ("energy_rate_profile_uuid" not in kwargs or
             kwargs["energy_rate_profile_uuid"] is None):
        raise D3ADeviceException(
            {"misconfiguration": ["energy_rate_profile must have a uuid."]})
    if key_in_dict_and_not_none_and_not_str_type(kwargs, "energy_rate_profile_uuid"):
        raise D3ADeviceException(
            {"misconfiguration": ["energy_rate_profile_uuid must have a string type."]})

    if key_in_dict_and_not_none(kwargs, "energy_buy_rate"):
        utils.validate_rate(kwargs["energy_buy_rate"])
    if key_in_dict_and_not_none(kwargs, "buying_rate_profile") and \
            ("buying_rate_profile_uuid" not in kwargs or
             kwargs["buying_rate_profile_uuid"] is None):
        raise D3ADeviceException(
            {"misconfiguration": ["buying_rate_profile must have a uuid."]})
    if key_in_dict_and_not_none_and_not_str_type(kwargs, "buying_rate_profile_uuid"):
        raise D3ADeviceException(
            {"misconfiguration": ["buying_rate_profile_uuid must have a string type."]})
