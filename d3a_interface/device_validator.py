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


GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings
PvSettings = ConstSettings.PVSettings
StorageSettings = ConstSettings.StorageSettings


def validate_load_device(**kwargs):
    if ("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) and \
            not (LoadSettings.AVG_POWER_RANGE.min <= kwargs["avg_power_W"] <=
                 LoadSettings.AVG_POWER_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"avg_power_W should be in between "
                                   f"{LoadSettings.AVG_POWER_RANGE.min} & "
                                   f"{LoadSettings.AVG_POWER_RANGE.max}."]})
    if (("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) or
        ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) or
        ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None)) \
            and ("daily_load_profile" in kwargs and kwargs["daily_load_profile"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"daily_load_profile shouldn't be set with"
                                   f"avg_power_W, hrs_per_day & hrs_of_day."]})
    if ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) and \
            not (LoadSettings.HOURS_RANGE.min <= kwargs["hrs_per_day"] <=
                 LoadSettings.HOURS_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"hrs_per_day should be in between "
                                   f"{LoadSettings.HOURS_RANGE.min} & "
                                   f"{LoadSettings.HOURS_RANGE.max}."]})
    if ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and not \
            (LoadSettings.FINAL_BUYING_RATE_RANGE.min <= kwargs["final_buying_rate"] <=
             LoadSettings.FINAL_BUYING_RATE_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"final_buying_rate should be in between "
                                   f"{LoadSettings.FINAL_BUYING_RATE_RANGE.min} & "
                                   f"{LoadSettings.FINAL_BUYING_RATE_RANGE.max}."]})
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            not (LoadSettings.INITIAL_BUYING_RATE_RANGE.min <= kwargs["initial_buying_rate"] <=
                 LoadSettings.INITIAL_BUYING_RATE_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_buying_rate should be in between "
                                   f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.min} & "
                                   f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.max}"]})
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]:
        raise D3ADeviceException({"mis_configuration": [f"initial_buying_rate should be "
                                                        f"less than final_buying_rate."]})
    if ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None) and \
            any([not LoadSettings.HOURS_RANGE.min <= h <= LoadSettings.HOURS_RANGE.max
                 for h in kwargs["hrs_of_day"]]):
        raise D3ADeviceException(
            {"mis_configuration": [f"hrs_of_day should be less between "
                                   f"{LoadSettings.HOURS_RANGE.min} & "
                                   f"{LoadSettings.HOURS_RANGE.max}."]})
    if ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None) and \
            ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) and \
            len(kwargs["hrs_of_day"]) < kwargs["hrs_per_day"]:
        raise D3ADeviceException(
            {"mis_configuration": [f"length of hrs_of_day list should be "
                                   f"greater than hrs_per_day."]})
    if ("energy_rate_increase_per_update" in kwargs and
        kwargs["energy_rate_increase_per_update"] is not None) and not \
            GeneralSettings.RATE_CHANGE_PER_UPDATE.min <= \
            kwargs["energy_rate_increase_per_update"] <= \
            GeneralSettings.RATE_CHANGE_PER_UPDATE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_increase_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            ("energy_rate_increase_per_update" in kwargs and
             kwargs["energy_rate_increase_per_update"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"fit_to_limit & energy_rate_increase_per_update"
                                   f"can't be set together."]})


def validate_pv_device(**kwargs):
    if ("panel_count" in kwargs and kwargs["panel_count"] is not None) and not \
            (PvSettings.PANEL_COUNT_RANGE.min <= kwargs["panel_count"] <=
             PvSettings.PANEL_COUNT_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"PV panel count should be in between "
                                   f"{PvSettings.PANEL_COUNT_RANGE.min} & "
                                   f"{PvSettings.PANEL_COUNT_RANGE.max}"]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and not \
            PvSettings.MIN_SELL_RATE_RANGE.min <= kwargs["final_selling_rate"] <= \
            PvSettings.MIN_SELL_RATE_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"final_selling_rate should be in between "
                                   f"{PvSettings.MIN_SELL_RATE_RANGE.min} & "
                                   f"{PvSettings.MIN_SELL_RATE_RANGE.max}"]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and not \
            (PvSettings.INITIAL_RATE_RANGE.min <= kwargs["initial_selling_rate"] <=
             PvSettings.INITIAL_RATE_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_selling_rate should be in between "
                                   f"{PvSettings.INITIAL_RATE_RANGE.min} & "
                                   f"{PvSettings.INITIAL_RATE_RANGE.max}"]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and \
            ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]:
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_selling_rate should be greater"
                                   f"than or equal to final_selling_rate."]})
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            ("energy_rate_decrease_per_update" in kwargs and
             kwargs["energy_rate_decrease_per_update"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"fit_to_limit & energy_rate_decrease_per_update"
                                   f"can't be set together."]})
    if ("energy_rate_decrease_per_update" in kwargs and
        kwargs["energy_rate_decrease_per_update"] is not None) and not \
            (GeneralSettings.RATE_CHANGE_PER_UPDATE.min <=
             kwargs["energy_rate_decrease_per_update"] <=
             GeneralSettings.RATE_CHANGE_PER_UPDATE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}"]})
    if ("max_panel_power_W" in kwargs and kwargs["max_panel_power_W"] is not None) and \
            not (PvSettings.MAX_PANEL_OUTPUT_W_RANGE.min <= kwargs["max_panel_power_W"] <=
                 PvSettings.MAX_PANEL_OUTPUT_W_RANGE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"max_panel_power_W should be in between "
                                   f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.min} & "
                                   f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.max}"]})
    if ("cloud_coverage" in kwargs and kwargs["cloud_coverage"] is not None) and \
            ("power_profile" in kwargs and kwargs["power_profile"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"cloud_coverage & power_profile can't be set together."]})


def validate_storage_device(**kwargs):
    if ("initial_soc" in kwargs and kwargs["initial_soc"] is not None) and not \
            StorageSettings.INITIAL_CHARGE_RANGE.min <= kwargs["initial_soc"] <= \
            StorageSettings.INITIAL_CHARGE_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_soc should be in between "
                                   f"{StorageSettings.INITIAL_CHARGE_RANGE.min} & "
                                   f"{StorageSettings.INITIAL_CHARGE_RANGE.max}."]})
    if ("min_allowed_soc" in kwargs and kwargs["min_allowed_soc"] is not None) and not \
            StorageSettings.MIN_SOC_RANGE.min <= kwargs["min_allowed_soc"] <= \
            StorageSettings.MIN_SOC_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"min_allowed_soc should be in between "
                                   f"{StorageSettings.MIN_SOC_RANGE.min} & "
                                   f"{StorageSettings.MIN_SOC_RANGE.max}."]})
    if ("initial_soc" in kwargs and kwargs["initial_soc"] is not None) and \
            ("min_allowed_soc" in kwargs and kwargs["min_allowed_soc"] is not None) and \
            kwargs["initial_soc"] < kwargs["min_allowed_soc"]:
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_soc should be greater"
                                   f"than or equal to min_allowed_soc."]})

    if ("battery_capacity_kWh" in kwargs and kwargs["battery_capacity_kWh"] is not None) and not \
            StorageSettings.CAPACITY_RANGE.min <= kwargs["battery_capacity_kWh"] <= \
            StorageSettings.CAPACITY_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"battery_capacity_kWh should be in between "
                                   f"{StorageSettings.CAPACITY_RANGE.min} & "
                                   f"{StorageSettings.CAPACITY_RANGE.max}."]})
    if ("max_abs_battery_power_kW" in kwargs and
        kwargs["max_abs_battery_power_kW"] is not None) and not \
            StorageSettings.MAX_ABS_POWER_RANGE.min <= kwargs["max_abs_battery_power_kW"] <= \
            StorageSettings.MAX_ABS_POWER_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"max_abs_battery_power_kW should be in between "
                                   f"{StorageSettings.MAX_ABS_POWER_RANGE.min} & "
                                   f"{StorageSettings.MAX_ABS_POWER_RANGE.max}."]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and not \
            StorageSettings.INITIAL_SELLING_RANGE.min <= kwargs["initial_selling_rate"] <= \
            StorageSettings.INITIAL_SELLING_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_selling_rate should be in between "
                                   f"{StorageSettings.INITIAL_SELLING_RANGE.min} & "
                                   f"{StorageSettings.INITIAL_SELLING_RANGE.max}."]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and not \
            StorageSettings.FINAL_SELLING_RANGE.min <= kwargs["final_selling_rate"] <= \
            StorageSettings.FINAL_SELLING_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"final_selling_rate should be in between "
                                   f"{StorageSettings.FINAL_SELLING_RANGE.min} & "
                                   f"{StorageSettings.FINAL_SELLING_RANGE.max}."]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and \
            ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]:
        raise D3ADeviceException({"mis_configuration": [f"initial_selling_rate should be greater"
                                                        f"than or equal to final_selling_rate."]})

    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and not \
            StorageSettings.INITIAL_BUYING_RANGE.min <= kwargs["initial_buying_rate"] <= \
            StorageSettings.INITIAL_BUYING_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_buying_rate should be in between "
                                   f"{StorageSettings.INITIAL_BUYING_RANGE.min} & "
                                   f"{StorageSettings.INITIAL_BUYING_RANGE.max}."]})

    if ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and not \
            StorageSettings.FINAL_BUYING_RANGE.min <= kwargs["final_buying_rate"] <= \
            StorageSettings.FINAL_BUYING_RANGE.max:
        raise D3ADeviceException(
            {"mis_configuration": [f"final_buying_rate should be in between "
                                   f"{StorageSettings.FINAL_BUYING_RANGE.min} & "
                                   f"{StorageSettings.FINAL_BUYING_RANGE.max}."]})
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]:
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_buying_rate should be less "
                                   f"than or equal to final_buying_rate."]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            kwargs["final_buying_rate"] > kwargs["final_selling_rate"]:
        raise D3ADeviceException(
            {"mis_configuration": [f"final_buying_rate should be less "
                                   f"than or equal to final_selling_rate."]})
    if ("energy_rate_increase_per_update" in kwargs and
        kwargs["energy_rate_increase_per_update"] is not None) and not \
            (GeneralSettings.RATE_CHANGE_PER_UPDATE.min <=
             kwargs["energy_rate_increase_per_update"] <=
             GeneralSettings.RATE_CHANGE_PER_UPDATE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_increase_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})
    if ("energy_rate_decrease_per_update" in kwargs and
        kwargs["energy_rate_decrease_per_update"] is not None) and not \
            (GeneralSettings.RATE_CHANGE_PER_UPDATE.min <=
             kwargs["energy_rate_decrease_per_update"] <=
             GeneralSettings.RATE_CHANGE_PER_UPDATE.max):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            ("energy_rate_increase_per_update" in kwargs and
             kwargs["energy_rate_increase_per_update"] is not None) or \
            ("energy_rate_decrease_per_update" in kwargs and
             kwargs["energy_rate_decrease_per_update"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"fit_to_limit & energy_rate_change_per_update "
                                   f"can't be set together."]})
