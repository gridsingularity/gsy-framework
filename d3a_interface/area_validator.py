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
from d3a_interface.device_validator import validate_range_limit
from d3a_interface.exceptions import D3AAreaException
from d3a_interface.utils import key_in_dict_and_not_none_and_greater_than_zero, \
    key_in_dict_and_not_none_and_negative, key_in_dict_and_not_none


GeneralSettings = ConstSettings.GeneralSettings
AreaSettings = ConstSettings.AreaSettings


def validate_area(**kwargs):
    if key_in_dict_and_not_none_and_greater_than_zero(kwargs, "grid_fee_constant") and \
            key_in_dict_and_not_none_and_greater_than_zero(kwargs, "grid_fee_percentage"):
        raise D3AAreaException("Cannot set both percentage and constant "
                               "grid fees on the same area.")
    if key_in_dict_and_not_none(kwargs, "grid_fee_percentage"):
        error_message = {"misconfiguration": [f"grid_fee_percentage should be in between "
                                              f"{AreaSettings.PERCENTAGE_FEE_LIMIT.min} & "
                                              f"{AreaSettings.PERCENTAGE_FEE_LIMIT.max}."]}
        validate_range_limit(AreaSettings.PERCENTAGE_FEE_LIMIT.min,
                             kwargs["grid_fee_percentage"],
                             AreaSettings.PERCENTAGE_FEE_LIMIT.max, error_message)

    elif key_in_dict_and_not_none(kwargs, "grid_fee_constant"):
        error_message = {"misconfiguration": [f"grid_fee_constant should be in between "
                                              f"{AreaSettings.CONSTANT_FEE_LIMIT.min} & "
                                              f"{AreaSettings.CONSTANT_FEE_LIMIT.max}."]}
        validate_range_limit(AreaSettings.CONSTANT_FEE_LIMIT.min,
                             kwargs["grid_fee_constant"],
                             AreaSettings.CONSTANT_FEE_LIMIT.max, error_message)

    if key_in_dict_and_not_none_and_negative(kwargs, "baseline_peak_energy_import_kWh"):
        raise D3AAreaException({"misconfiguration": [f"baseline_peak_energy_import_kWh must be a "
                                                     f"positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "baseline_peak_energy_export_kWh"):
        raise D3AAreaException({"misconfiguration": [f"baseline_peak_energy_export_kWh must be a "
                                                     f"positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "import_capacity_kVA"):
        raise D3AAreaException(
            {"misconfiguration": [f"import_capacity_kVA must be a positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "export_capacity_kVA"):
        raise D3AAreaException({"misconfiguration": [f"export_capacity_kVA must be a "
                                                     f"positive value."]})
