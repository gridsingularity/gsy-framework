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


GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings
PvSettings = ConstSettings.PVSettings
StorageSettings = ConstSettings.StorageSettings
CepSettings = ConstSettings.CommercialProducerSettings


def validate_load_device(**kwargs):
    if ("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) and \
            not _validate_range_limit(LoadSettings.AVG_POWER_RANGE.initial,
                                      kwargs["avg_power_W"],
                                      LoadSettings.AVG_POWER_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"avg_power_W should be in between "
                                   f"{LoadSettings.AVG_POWER_RANGE.initial} & "
                                   f"{LoadSettings.AVG_POWER_RANGE.final}."]})
    if (("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) or
        ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) or
        ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None)) \
            and ("daily_load_profile" in kwargs and kwargs["daily_load_profile"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"daily_load_profile shouldn't be set with"
                                   f"avg_power_W, hrs_per_day & hrs_of_day."]})
    if ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) and \
            not _validate_range_limit(LoadSettings.HOURS_RANGE.initial,
                                      kwargs["hrs_per_day"],
                                      LoadSettings.HOURS_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"hrs_per_day should be in between "
                                   f"{LoadSettings.HOURS_RANGE.initial} & "
                                   f"{LoadSettings.HOURS_RANGE.final}."]})
    if ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and not \
            _validate_range_limit(LoadSettings.FINAL_BUYING_RATE_RANGE.initial,
                                  kwargs["final_buying_rate"],
                                  LoadSettings.FINAL_BUYING_RATE_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"final_buying_rate should be in between "
                                   f"{LoadSettings.FINAL_BUYING_RATE_RANGE.initial} & "
                                   f"{LoadSettings.FINAL_BUYING_RATE_RANGE.final}."]})
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            not _validate_range_limit(LoadSettings.INITIAL_BUYING_RATE_RANGE.initial,
                                      kwargs["initial_buying_rate"],
                                      LoadSettings.INITIAL_BUYING_RATE_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_buying_rate should be in between "
                                   f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.initial} & "
                                   f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.final}"]})
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
        raise D3ADeviceException({"mis_configuration": [f"initial_buying_rate should be "
                                                        f"less than final_buying_rate."]})
    if ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None) and \
            any([not LoadSettings.HOURS_RANGE.initial <= h <= LoadSettings.HOURS_RANGE.final
                 for h in kwargs["hrs_of_day"]]):
        raise D3ADeviceException(
            {"mis_configuration": [f"hrs_of_day should be less between "
                                   f"{LoadSettings.HOURS_RANGE.initial} & "
                                   f"{LoadSettings.HOURS_RANGE.final}."]})
    if ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None) and \
            ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) and \
            (len(kwargs["hrs_of_day"]) < kwargs["hrs_per_day"]):
        raise D3ADeviceException(
            {"mis_configuration": [f"length of hrs_of_day list should be "
                                   f"greater than hrs_per_day."]})
    if ("energy_rate_increase_per_update" in kwargs and
        kwargs["energy_rate_increase_per_update"] is not None) and not \
            _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE.initial,
                                  kwargs["energy_rate_increase_per_update"],
                                  GeneralSettings.RATE_CHANGE_PER_UPDATE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_increase_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.initial} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.final}."]})
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            ("energy_rate_increase_per_update" in kwargs and
             kwargs["energy_rate_increase_per_update"] is not None):
        raise D3ADeviceException(
            {"mis_configuration": [f"fit_to_limit & energy_rate_increase_per_update"
                                   f"can't be set together."]})


def validate_pv_device(**kwargs):
    if ("panel_count" in kwargs and kwargs["panel_count"] is not None) and not \
            _validate_range_limit(PvSettings.PANEL_COUNT_RANGE.initial,
                                  kwargs["panel_count"],
                                  PvSettings.PANEL_COUNT_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"PV panel count should be in between "
                                   f"{PvSettings.PANEL_COUNT_RANGE.initial} & "
                                   f"{PvSettings.PANEL_COUNT_RANGE.final}"]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and not \
            _validate_range_limit(PvSettings.MIN_SELL_RATE_RANGE.initial,
                                  kwargs["final_selling_rate"],
                                  PvSettings.MIN_SELL_RATE_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"final_selling_rate should be in between "
                                   f"{PvSettings.MIN_SELL_RATE_RANGE.initial} & "
                                   f"{PvSettings.MIN_SELL_RATE_RANGE.final}"]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and not \
            _validate_range_limit(PvSettings.INITIAL_RATE_RANGE.initial,
                                  kwargs["initial_selling_rate"],
                                  PvSettings.INITIAL_RATE_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_selling_rate should be in between "
                                   f"{PvSettings.INITIAL_RATE_RANGE.initial} & "
                                   f"{PvSettings.INITIAL_RATE_RANGE.final}"]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and \
            ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            (kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
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
            _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE.initial,
                                  kwargs["energy_rate_decrease_per_update"],
                                  GeneralSettings.RATE_CHANGE_PER_UPDATE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.initial} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.final}"]})
    if ("max_panel_power_W" in kwargs and kwargs["max_panel_power_W"] is not None) and \
            not _validate_range_limit(PvSettings.MAX_PANEL_OUTPUT_W_RANGE.initial,
                                      kwargs["max_panel_power_W"],
                                      PvSettings.MAX_PANEL_OUTPUT_W_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"max_panel_power_W should be in between "
                                   f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.initial} & "
                                   f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.final}"]})
    if "cloud_coverage" in kwargs and kwargs["cloud_coverage"] is not None:
        if (kwargs["cloud_coverage"] != 4) and \
           ("power_profile" in kwargs and kwargs["power_profile"] is not None):
            raise D3ADeviceException(
                {"mis_configuration": [f"cloud_coverage (if values 0-3) & "
                                       f"power_profile can't be set together."]})


def validate_storage_device(**kwargs):
    if ("initial_soc" in kwargs and kwargs["initial_soc"] is not None) and not \
            _validate_range_limit(StorageSettings.INITIAL_CHARGE_RANGE.initial,
                                  kwargs["initial_soc"],
                                  StorageSettings.INITIAL_CHARGE_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_soc should be in between "
                                   f"{StorageSettings.INITIAL_CHARGE_RANGE.initial} & "
                                   f"{StorageSettings.INITIAL_CHARGE_RANGE.final}."]})
    if ("min_allowed_soc" in kwargs and kwargs["min_allowed_soc"] is not None) and not \
            _validate_range_limit(StorageSettings.MIN_SOC_RANGE.initial,
                                  kwargs["min_allowed_soc"],
                                  StorageSettings.MIN_SOC_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"min_allowed_soc should be in between "
                                   f"{StorageSettings.MIN_SOC_RANGE.initial} & "
                                   f"{StorageSettings.MIN_SOC_RANGE.final}."]})
    if ("initial_soc" in kwargs and kwargs["initial_soc"] is not None) and \
            ("min_allowed_soc" in kwargs and kwargs["min_allowed_soc"] is not None) and \
            (kwargs["initial_soc"] < kwargs["min_allowed_soc"]):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_soc should be greater"
                                   f"than or equal to min_allowed_soc."]})

    if ("battery_capacity_kWh" in kwargs and kwargs["battery_capacity_kWh"] is not None) and not \
            _validate_range_limit(StorageSettings.CAPACITY_RANGE.initial,
                                  kwargs["battery_capacity_kWh"],
                                  StorageSettings.CAPACITY_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"battery_capacity_kWh should be in between "
                                   f"{StorageSettings.CAPACITY_RANGE.initial} & "
                                   f"{StorageSettings.CAPACITY_RANGE.final}."]})
    if ("max_abs_battery_power_kW" in kwargs and
        kwargs["max_abs_battery_power_kW"] is not None) and not \
            _validate_range_limit(StorageSettings.MAX_ABS_POWER_RANGE.initial,
                                  kwargs["max_abs_battery_power_kW"],
                                  StorageSettings.MAX_ABS_POWER_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"max_abs_battery_power_kW should be in between "
                                   f"{StorageSettings.MAX_ABS_POWER_RANGE.initial} & "
                                   f"{StorageSettings.MAX_ABS_POWER_RANGE.final}."]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and not \
            _validate_range_limit(StorageSettings.INITIAL_SELLING_RANGE.initial,
                                  kwargs["initial_selling_rate"],
                                  StorageSettings.INITIAL_SELLING_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_selling_rate should be in between "
                                   f"{StorageSettings.INITIAL_SELLING_RANGE.initial} & "
                                   f"{StorageSettings.INITIAL_SELLING_RANGE.final}."]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and not \
            _validate_range_limit(StorageSettings.FINAL_SELLING_RANGE.initial,
                                  kwargs["final_selling_rate"],
                                  StorageSettings.FINAL_SELLING_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"final_selling_rate should be in between "
                                   f"{StorageSettings.FINAL_SELLING_RANGE.initial} & "
                                   f"{StorageSettings.FINAL_SELLING_RANGE.final}."]})
    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and \
            ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            (kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
        raise D3ADeviceException({"mis_configuration": [f"initial_selling_rate should be greater"
                                                        f"than or equal to final_selling_rate."]})

    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and not \
            _validate_range_limit(StorageSettings.INITIAL_BUYING_RANGE.initial,
                                  kwargs["initial_buying_rate"],
                                  StorageSettings.INITIAL_BUYING_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_buying_rate should be in between "
                                   f"{StorageSettings.INITIAL_BUYING_RANGE.initial} & "
                                   f"{StorageSettings.INITIAL_BUYING_RANGE.final}."]})

    if ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and not \
            (StorageSettings.FINAL_BUYING_RANGE.initial <= kwargs["final_buying_rate"] <=
             StorageSettings.FINAL_BUYING_RANGE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"final_buying_rate should be in between "
                                   f"{StorageSettings.FINAL_BUYING_RANGE.initial} & "
                                   f"{StorageSettings.FINAL_BUYING_RANGE.final}."]})
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
        raise D3ADeviceException(
            {"mis_configuration": [f"initial_buying_rate should be less "
                                   f"than or equal to final_buying_rate."]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["final_buying_rate"] > kwargs["final_selling_rate"]):
        raise D3ADeviceException(
            {"mis_configuration": [f"final_buying_rate should be less "
                                   f"than or equal to final_selling_rate."]})
    if ("energy_rate_increase_per_update" in kwargs and
        kwargs["energy_rate_increase_per_update"] is not None) and not \
            _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE.initial,
                                  kwargs["energy_rate_increase_per_update"],
                                  GeneralSettings.RATE_CHANGE_PER_UPDATE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_increase_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.initial} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.final}."]})
    if ("energy_rate_decrease_per_update" in kwargs and
        kwargs["energy_rate_decrease_per_update"] is not None) and not \
            _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE.initial,
                                  kwargs["energy_rate_decrease_per_update"],
                                  GeneralSettings.RATE_CHANGE_PER_UPDATE.final):
        raise D3ADeviceException(
            {"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.initial} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.final}."]})
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            (("energy_rate_increase_per_update" in kwargs and
              kwargs["energy_rate_increase_per_update"] is not None) or
             ("energy_rate_decrease_per_update" in kwargs and
              kwargs["energy_rate_decrease_per_update"] is not None)):
        raise D3ADeviceException(
            {"mis_configuration": [f"fit_to_limit & energy_rate_change_per_update "
                                   f"can't be set together."]})


def _validate_rate(energy_rate):
    if not _validate_range_limit(CepSettings.ENERGY_RATE_RANGE.initial, energy_rate,
                                 CepSettings.ENERGY_RATE_RANGE.final):
        raise D3ADeviceException(
            {
                "misconfiguration": [f"energy_rate should be in between "
                                     f"{CepSettings.ENERGY_RATE_RANGE.initial} & "
                                     f"{CepSettings.ENERGY_RATE_RANGE.final}."]})


def _validate_rate_profile(energy_rate_profile):
    for date, value in energy_rate_profile.items():
        value = float(value) if type(value) == str else value
        if not _validate_range_limit(CepSettings.ENERGY_RATE_RANGE.initial, value,
                                     CepSettings.ENERGY_RATE_RANGE.final):
            raise D3ADeviceException(
                {"misconfiguration": [f"energy_rate should at time: {date} be in between "
                                      f"{CepSettings.ENERGY_RATE_RANGE.initial} & "
                                      f"{CepSettings.ENERGY_RATE_RANGE.final}."]})


def validate_commercial_producer(**kwargs):
    if "energy_rate" in kwargs and kwargs["energy_rate"] is not None:
        if isinstance(kwargs["energy_rate"], (float, int)):
            _validate_rate(kwargs["energy_rate"])
        elif isinstance(kwargs["energy_rate"], str):
            _validate_rate_profile(ast.literal_eval(kwargs["energy_rate"]))
        elif isinstance(kwargs["energy_rate"], dict):
            _validate_rate_profile(kwargs["energy_rate"])
        else:
            raise D3ADeviceException({"misconfiguration": [f"energy_rate has an invalid type."]})


def validate_market_maker(**kwargs):
    if "energy_rate" in kwargs and kwargs["energy_rate"] is not None:
        if isinstance(kwargs["energy_rate"], (float, int)):
            _validate_rate(kwargs["energy_rate"])
        elif isinstance(kwargs["energy_rate"], str):
            _validate_rate_profile(ast.literal_eval(kwargs["energy_rate"]))
        elif isinstance(ast.literal_eval(kwargs["energy_rate"]), dict):
            _validate_rate_profile(kwargs["energy_rate"])
        else:
            raise D3ADeviceException({"misconfiguration": [f"energy_rate has an invalid type."]})
    if "energy_rate_profile" in kwargs and kwargs["energy_rate_profile"] is not None and \
            ("energy_rate_profile_uuid" not in kwargs or
             kwargs["energy_rate_profile_uuid"] is None):
        raise D3ADeviceException(
            {"misconfiguration": [f"energy_rate_profile must have a uuid."]})
    if "grid_connected" in kwargs and kwargs["grid_connected"] is not None and \
            not isinstance(kwargs["grid_connected"], bool):
        raise D3ADeviceException(
            {"misconfiguration": [f"grid_connected must be a boolean value."]})


def validate_finite_diesel_generator(**kwargs):
    if "max_available_power_kW" in kwargs and kwargs["max_available_power_kW"] is not None:
        if isinstance(kwargs["max_available_power_kW"], (int, float)):
            if not _validate_range_limit(CepSettings.MAX_POWER_KW_RANGE.initial,
                                         kwargs["max_available_power_kW"],
                                         CepSettings.MAX_POWER_KW_RANGE.final):
                raise D3ADeviceException(
                    {"misconfiguration": [f"max_available_power_kW should be in between "
                                          f"{CepSettings.MAX_POWER_KW_RANGE.initial} & "
                                          f"{CepSettings.MAX_POWER_KW_RANGE.final}."]})
        elif isinstance(kwargs["max_available_power_kW"], dict):
            for date, value in kwargs["max_available_power_kW"].items():
                if not _validate_range_limit(CepSettings.MAX_POWER_KW_RANGE.initial, value,
                                             CepSettings.MAX_POWER_KW_RANGE.final):
                    raise D3ADeviceException(
                        {
                            "misconfiguration": [f"max_available_power_kW should be in between "
                                                 f"{CepSettings.MAX_POWER_KW_RANGE.initial} & "
                                                 f"{CepSettings.MAX_POWER_KW_RANGE.final}."]})
        else:
            raise D3ADeviceException({"misconfiguration": [f"max_available_power_kW has an "
                                                           f"invalid type. "]})

    validate_commercial_producer(**kwargs)


def _validate_range_limit(initial_limit, value, final_limit):
    return False if not initial_limit <= value <= final_limit else True
