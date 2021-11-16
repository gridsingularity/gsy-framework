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

from gsy_framework.constants_limits import ConstSettings
from gsy_framework.validators.utils import validate_range_limit
from gsy_framework.exceptions import GSyAreaException
from gsy_framework.utils import (
    key_in_dict_and_not_none, key_in_dict_and_not_none_and_greater_than_zero,
    key_in_dict_and_not_none_and_negative)


GeneralSettings = ConstSettings.GeneralSettings
AreaSettings = ConstSettings.AreaSettings


def validate_area(**kwargs):
    if key_in_dict_and_not_none_and_greater_than_zero(kwargs, "grid_fee_constant") and \
            key_in_dict_and_not_none_and_greater_than_zero(kwargs, "grid_fee_percentage"):
        raise GSyAreaException("Cannot set both percentage and constant "
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
        raise GSyAreaException({"misconfiguration": ["baseline_peak_energy_import_kWh must be a "
                                                     "positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "baseline_peak_energy_export_kWh"):
        raise GSyAreaException({"misconfiguration": ["baseline_peak_energy_export_kWh must be a "
                                                     "positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "import_capacity_kVA"):
        raise GSyAreaException(
            {"misconfiguration": ["import_capacity_kVA must be a positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "export_capacity_kVA"):
        raise GSyAreaException({"misconfiguration": ["export_capacity_kVA must be a "
                                                     "positive value."]})
