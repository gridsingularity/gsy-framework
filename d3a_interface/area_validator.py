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

from d3a_interface.constants_limits import ConstSettings, RangeLimit
from d3a_interface.device_validator import validate_range_limit
from d3a_interface.exceptions import D3AException
from d3a_interface.utils import key_in_dict_and_not_none, key_in_dict_and_not_none_and_negative


GeneralSettings = ConstSettings.GeneralSettings
AreaSettings = ConstSettings.AreaSettings


CONSTANT_FEE_LIMIT = RangeLimit(0, 200)


def validate_area(**kwargs):
    is_percentage_fee = key_in_dict_and_not_none(kwargs, "grid_fee_percentage")
    is_constant_fee = key_in_dict_and_not_none(kwargs, "grid_fee_constant")
    if is_percentage_fee and is_constant_fee:
        raise D3AException("Cannot set both percentage and constant grid fees on the same area.")
    if is_percentage_fee:
        error_message = {"misconfiguration": [f"grid_fee_percentage should be in between "
                                              f"{AreaSettings.GRID_FEE_PERCENTAGE_LIMIT.min} & "
                                              f"{AreaSettings.GRID_FEE_PERCENTAGE_LIMIT.max}."]}
        validate_range_limit(AreaSettings.GRID_FEE_PERCENTAGE_LIMIT.min,
                             kwargs["grid_fee_percentage"],
                             AreaSettings.GRID_FEE_PERCENTAGE_LIMIT.max, error_message)

    elif is_constant_fee:
        error_message = {"misconfiguration": [f"grid_fee_constant should be in between "
                                              f"{CONSTANT_FEE_LIMIT.min} & "
                                              f"{CONSTANT_FEE_LIMIT.max}."]}
        validate_range_limit(CONSTANT_FEE_LIMIT.min,
                             kwargs["grid_fee_constant"],
                             CONSTANT_FEE_LIMIT.max, error_message)

    if key_in_dict_and_not_none_and_negative(kwargs, "baseline_peak_energy_import_kWh"):
        raise D3AException({"misconfiguration": [f"baseline_peak_energy_import_kWh must be a "
                                                 f"positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "baseline_peak_energy_export_kWh"):
        raise D3AException({"misconfiguration": [f"baseline_peak_energy_export_kWh must be a "
                                                 f"positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "import_capacity_kVA"):
        raise D3AException(
            {"misconfiguration": [f"import_capacity_kVA must be a positive value."]})
    if key_in_dict_and_not_none_and_negative(kwargs, "export_capacity_kVA"):
        raise D3AException({"misconfiguration": [f"export_capacity_kVA must be a "
                                                 f"positive value."]})
