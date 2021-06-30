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
from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException
from d3a_interface.validators import utils
from d3a_interface.validators.cep_validator import validate_commercial_producer

CepSettings = ConstSettings.CommercialProducerSettings


def validate_finite_diesel_generator(**kwargs):
    if "max_available_power_kW" in kwargs and kwargs["max_available_power_kW"] is not None:
        if isinstance(kwargs["max_available_power_kW"], (int, float)):
            error_message = \
                {"misconfiguration": ["max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            utils.validate_range_limit(
                CepSettings.MAX_POWER_KW_LIMIT.min,
                kwargs["max_available_power_kW"],
                CepSettings.MAX_POWER_KW_LIMIT.max,
                error_message)
        elif isinstance(kwargs["max_available_power_kW"], dict):
            error_message = \
                {"misconfiguration": ["max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            for _, value in kwargs["max_available_power_kW"].items():
                utils.validate_range_limit(
                    CepSettings.MAX_POWER_KW_LIMIT.min, value,
                    CepSettings.MAX_POWER_KW_LIMIT.max, error_message)
        else:
            raise D3ADeviceException({
                "misconfiguration": ["max_available_power_kW has an invalid type. "]})

    validate_commercial_producer(**kwargs)
