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
import ast

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException

CepSettings = ConstSettings.CommercialProducerSettings


# TODO: put this in the base class? Better: create a RangeLimitValidator class
def validate_range_limit(initial_limit, value, final_limit, error_message):
    if not initial_limit <= value <= final_limit:
        raise D3ADeviceException(error_message)


def validate_energy_rate(**kwargs):
    if "energy_rate" in kwargs and kwargs["energy_rate"] is not None:
        if isinstance(kwargs["energy_rate"], (float, int)):
            validate_rate(kwargs["energy_rate"])
        elif isinstance(kwargs["energy_rate"], str):
            _validate_rate_profile(ast.literal_eval(kwargs["energy_rate"]))
        elif isinstance(kwargs["energy_rate"], dict):
            _validate_rate_profile(kwargs["energy_rate"])
        else:
            raise D3ADeviceException({"misconfiguration": [f"energy_rate has an invalid type."]})


def validate_rate(energy_rate):
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
