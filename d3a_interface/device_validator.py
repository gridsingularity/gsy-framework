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
    if ("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None):
        error_message = {"misconfiguration": [f"avg_power_W should be in between "
                                              f"{LoadSettings.AVG_POWER_LIMIT.min} & "
                                              f"{LoadSettings.AVG_POWER_LIMIT.max}."]}
        _validate_range_limit(LoadSettings.AVG_POWER_LIMIT.min,
                              kwargs["avg_power_W"],
                              LoadSettings.AVG_POWER_LIMIT.max, error_message)

    if (("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) or
        ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) or
        ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None)) \
            and ("daily_load_profile" in kwargs and kwargs["daily_load_profile"] is not None):
        raise D3ADeviceException(
            {"misconfiguration": [f"daily_load_profile shouldn't be set with "
                                  f"avg_power_W, hrs_per_day & hrs_of_day."]})
    if "hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None:
        error_message = {"misconfiguration": [f"hrs_per_day should be in between "
                                              f"{LoadSettings.HOURS_LIMIT.min} & "
                                              f"{LoadSettings.HOURS_LIMIT.max}."]}
        _validate_range_limit(LoadSettings.HOURS_LIMIT.min,
                              kwargs["hrs_per_day"],
                              LoadSettings.HOURS_LIMIT.max, error_message)
    if "final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None:
        error_message = {"misconfiguration": [f"final_buying_rate should be in between "
                                              f"{LoadSettings.FINAL_BUYING_RATE_LIMIT.min} & "
                                              f"{LoadSettings.FINAL_BUYING_RATE_LIMIT.max}."]}
        _validate_range_limit(LoadSettings.FINAL_BUYING_RATE_LIMIT.min,
                              kwargs["final_buying_rate"],
                              LoadSettings.FINAL_BUYING_RATE_LIMIT.max, error_message)
    if "initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None:
        error_message = \
            {"misconfiguration": [f"initial_buying_rate should be in between "
                                  f"{LoadSettings.INITIAL_BUYING_RATE_LIMIT.min} & "
                                  f"{LoadSettings.INITIAL_BUYING_RATE_LIMIT.max}"]}
        _validate_range_limit(LoadSettings.INITIAL_BUYING_RATE_LIMIT.min,
                              kwargs["initial_buying_rate"],
                              LoadSettings.INITIAL_BUYING_RATE_LIMIT.max, error_message)

    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
        raise D3ADeviceException({"misconfiguration": [f"initial_buying_rate should be "
                                                       f"less than final_buying_rate/"
                                                       f"market_maker_rate. Please adapt the "
                                                       f"market_maker_rate of the configuration "
                                                       f"or the initial_buying_rate"]})
    if ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None) and \
            any([not LoadSettings.HOURS_LIMIT.min <= h <= LoadSettings.HOURS_LIMIT.max
                 for h in kwargs["hrs_of_day"]]):
        raise D3ADeviceException(
            {"misconfiguration": [f"hrs_of_day should be less between "
                                  f"{LoadSettings.HOURS_LIMIT.min} & "
                                  f"{LoadSettings.HOURS_LIMIT.max}."]})
    if ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None) and \
            ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) and \
            (len(kwargs["hrs_of_day"]) < kwargs["hrs_per_day"]):
        raise D3ADeviceException(
            {"misconfiguration": [f"length of hrs_of_day list should be "
                                  f"greater than hrs_per_day."]})
    if "energy_rate_increase_per_update" in kwargs and \
            kwargs["energy_rate_increase_per_update"] is not None:
        error_message = \
            {"misconfiguration": [f"energy_rate_increase_per_update should be in between "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
        _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                              kwargs["energy_rate_increase_per_update"],
                              GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            ("energy_rate_increase_per_update" in kwargs and
             kwargs["energy_rate_increase_per_update"] is not None):
        raise D3ADeviceException(
            {"misconfiguration": [f"fit_to_limit & energy_rate_increase_per_update "
                                  f"can't be set together."]})

    if (("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) or
            ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) or
            ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None)) and \
            ("daily_load_profile" in kwargs and kwargs["daily_load_profile"] is not None):
        raise D3ADeviceException(
            {"misconfiguration": [f"daily_load_profile and all or one [hrs_per_day, hrs_of_day, "
                                  f"avg_power_W] can't be set together."]})


def validate_pv_device(**kwargs):
    if ("panel_count" in kwargs and kwargs["panel_count"] is not None):
        error_message = \
            {"misconfiguration": [f"PV panel count should be in between "
                                  f"{PvSettings.PANEL_COUNT_LIMIT.min} & "
                                  f"{PvSettings.PANEL_COUNT_LIMIT.max}"]}
        _validate_range_limit(PvSettings.PANEL_COUNT_LIMIT.min,
                              kwargs["panel_count"],
                              PvSettings.PANEL_COUNT_LIMIT.max, error_message)

    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None):
        error_message = {"misconfiguration": [f"final_selling_rate should be in between "
                                              f"{PvSettings.FINAL_SELLING_RATE_LIMIT.min} & "
                                              f"{PvSettings.FINAL_SELLING_RATE_LIMIT.max}"]}
        _validate_range_limit(PvSettings.FINAL_SELLING_RATE_LIMIT.min,
                              kwargs["final_selling_rate"],
                              PvSettings.FINAL_SELLING_RATE_LIMIT.max, error_message)

    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None):
        error_message = {"misconfiguration": [f"initial_selling_rate should be in between "
                                              f"{PvSettings.INITIAL_SELLING_RATE_LIMIT.min} & "
                                              f"{PvSettings.INITIAL_SELLING_RATE_LIMIT.max}"]}
        _validate_range_limit(PvSettings.INITIAL_SELLING_RATE_LIMIT.min,
                              kwargs["initial_selling_rate"],
                              PvSettings.INITIAL_SELLING_RATE_LIMIT.max, error_message)

    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and \
            ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            (kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
        raise D3ADeviceException(
            {"misconfiguration": [f"initial_selling_rate/market_maker_rate should be greater "
                                  f"than or equal to final_selling_rate. Please adapt the "
                                  f"market_maker_rate of the configuration or the "
                                  f"initial_selling_rate"]})
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            ("energy_rate_decrease_per_update" in kwargs and
             kwargs["energy_rate_decrease_per_update"] is not None):
        raise D3ADeviceException(
            {"misconfiguration": [f"fit_to_limit & energy_rate_decrease_per_update "
                                  f"can't be set together."]})
    if "energy_rate_decrease_per_update" in kwargs and \
            kwargs["energy_rate_decrease_per_update"] is not None:
        error_message = \
            {"misconfiguration": [f"energy_rate_decrease_per_update should be in between "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}"]}
        _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                              kwargs["energy_rate_decrease_per_update"],
                              GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)
    if "max_panel_power_W" in kwargs and kwargs["max_panel_power_W"] is not None:
        error_message = \
            {"misconfiguration": [f"max_panel_power_W should be in between "
                                  f"{PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.min} & "
                                  f"{PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.max}"]}
        _validate_range_limit(PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.min,
                              kwargs["max_panel_power_W"],
                              PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.max, error_message)
    if "cloud_coverage" in kwargs and kwargs["cloud_coverage"] is not None:
        if (kwargs["cloud_coverage"] != 4) and \
           ("power_profile" in kwargs and kwargs["power_profile"] is not None):
            raise D3ADeviceException(
                {"misconfiguration": [f"cloud_coverage (if values 0-3) & "
                                      f"power_profile can't be set together."]})


def validate_storage_device(**kwargs):
    if "initial_soc" in kwargs and kwargs["initial_soc"] is not None:
        error_message = \
            {"misconfiguration": [f"initial_soc should be in between "
                                  f"{StorageSettings.INITIAL_CHARGE_LIMIT.min} & "
                                  f"{StorageSettings.INITIAL_CHARGE_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.INITIAL_CHARGE_LIMIT.min,
                              kwargs["initial_soc"],
                              StorageSettings.INITIAL_CHARGE_LIMIT.max, error_message)

    if ("min_allowed_soc" in kwargs and kwargs["min_allowed_soc"] is not None):
        error_message = \
            {"misconfiguration": [f"min_allowed_soc should be in between "
                                  f"{StorageSettings.MIN_SOC_LIMIT.min} & "
                                  f"{StorageSettings.MIN_SOC_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.MIN_SOC_LIMIT.min,
                              kwargs["min_allowed_soc"],
                              StorageSettings.MIN_SOC_LIMIT.max, error_message)

    if ("initial_soc" in kwargs and kwargs["initial_soc"] is not None) and \
            ("min_allowed_soc" in kwargs and kwargs["min_allowed_soc"] is not None) and \
            (kwargs["initial_soc"] < kwargs["min_allowed_soc"]):
        raise D3ADeviceException(
            {"misconfiguration": [f"initial_soc should be greater "
                                  f"than or equal to min_allowed_soc."]})

    if "battery_capacity_kWh" in kwargs and kwargs["battery_capacity_kWh"] is not None:
        error_message = \
            {"misconfiguration": [f"battery_capacity_kWh should be in between "
                                  f"{StorageSettings.CAPACITY_LIMIT.min} & "
                                  f"{StorageSettings.CAPACITY_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.CAPACITY_LIMIT.min,
                              kwargs["battery_capacity_kWh"],
                              StorageSettings.CAPACITY_LIMIT.max, error_message)
    if "max_abs_battery_power_kW" in kwargs and kwargs["max_abs_battery_power_kW"] is not None:
        error_message = \
            {"misconfiguration": [f"max_abs_battery_power_kW should be in between "
                                  f"{StorageSettings.MAX_ABS_POWER_RANGE.initial} & "
                                  f"{StorageSettings.MAX_ABS_POWER_RANGE.final}."]}
        _validate_range_limit(StorageSettings.MAX_ABS_POWER_RANGE.initial,
                              kwargs["max_abs_battery_power_kW"],
                              StorageSettings.MAX_ABS_POWER_RANGE.final, error_message)

    if "initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None:
        error_message = \
            {"misconfiguration": [f"initial_selling_rate should be in between "
                                  f"{StorageSettings.INITIAL_SELLING_RATE_LIMIT.min} & "
                                  f"{StorageSettings.INITIAL_SELLING_RATE_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.INITIAL_SELLING_RATE_LIMIT.min,
                              kwargs["initial_selling_rate"],
                              StorageSettings.INITIAL_SELLING_RATE_LIMIT.max, error_message)

    if "final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None:
        error_message = \
            {"misconfiguration": [f"final_selling_rate should be in between "
                                  f"{StorageSettings.FINAL_SELLING_RATE_LIMIT.min} & "
                                  f"{StorageSettings.FINAL_SELLING_RATE_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.FINAL_SELLING_RATE_LIMIT.min,
                              kwargs["final_selling_rate"],
                              StorageSettings.FINAL_SELLING_RATE_LIMIT.max, error_message)

    if ("initial_selling_rate" in kwargs and kwargs["initial_selling_rate"] is not None) and \
            ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            (kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
        raise D3ADeviceException({"misconfiguration": [f"initial_selling_rate should be greater "
                                                       f"than or equal to final_selling_rate."]})

    if "initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None:
        error_message = \
            {"misconfiguration": [f"initial_buying_rate should be in between "
                                  f"{StorageSettings.INITIAL_BUYING_RATE_LIMIT.min} & "
                                  f"{StorageSettings.INITIAL_BUYING_RATE_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.INITIAL_BUYING_RATE_LIMIT.min,
                              kwargs["initial_buying_rate"],
                              StorageSettings.INITIAL_BUYING_RATE_LIMIT.max, error_message)

    if ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None):
        error_message = {"misconfiguration": [f"final_buying_rate should be in between "
                                              f"{StorageSettings.FINAL_BUYING_RATE_LIMIT.min} & "
                                              f"{StorageSettings.FINAL_BUYING_RATE_LIMIT.max}."]}
        _validate_range_limit(StorageSettings.FINAL_BUYING_RATE_LIMIT.min,
                              kwargs["final_buying_rate"],
                              StorageSettings.FINAL_BUYING_RATE_LIMIT.max, error_message)
    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
        raise D3ADeviceException(
            {"misconfiguration": [f"initial_buying_rate should be less "
                                  f"than or equal to final_buying_rate."]})
    if ("final_selling_rate" in kwargs and kwargs["final_selling_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["final_buying_rate"] > kwargs["final_selling_rate"]):
        raise D3ADeviceException(
            {"misconfiguration": [f"final_buying_rate should be less "
                                  f"than or equal to final_selling_rate."]})

    if "energy_rate_increase_per_update" in kwargs and \
            kwargs["energy_rate_increase_per_update"] is not None:
        error_message = \
            {"misconfiguration": [f"energy_rate_increase_per_update should be in between "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
        _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                              kwargs["energy_rate_increase_per_update"],
                              GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

    if "energy_rate_decrease_per_update" in kwargs and \
            kwargs["energy_rate_decrease_per_update"] is not None:
        error_message = \
            {"misconfiguration": [f"energy_rate_decrease_per_update should be in between "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
        _validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                              kwargs["energy_rate_decrease_per_update"],
                              GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)
    if ("fit_to_limit" in kwargs and kwargs["fit_to_limit"] is True) and \
            (("energy_rate_increase_per_update" in kwargs and
              kwargs["energy_rate_increase_per_update"] is not None) or
             ("energy_rate_decrease_per_update" in kwargs and
              kwargs["energy_rate_decrease_per_update"] is not None)):
        raise D3ADeviceException(
            {"misconfiguration": [f"fit_to_limit & energy_rate_change_per_update "
                                  f"can't be set together."]})


def _validate_rate(energy_rate):
    error_message = \
        {"misconfiguration": [f"energy_rate should be in between "
                              f"{CepSettings.ENERGY_RATE_LIMIT.min} & "
                              f"{CepSettings.ENERGY_RATE_LIMIT.max}."]}
    _validate_range_limit(CepSettings.ENERGY_RATE_LIMIT.min, energy_rate,
                          CepSettings.ENERGY_RATE_LIMIT.max, error_message)


def _validate_rate_profile(energy_rate_profile):
    for date, value in energy_rate_profile.items():
        value = float(value) if type(value) == str else value
        error_message = \
            {"misconfiguration": [f"energy_rate should at time: {date} be in between "
                                  f"{CepSettings.ENERGY_RATE_LIMIT.min} & "
                                  f"{CepSettings.ENERGY_RATE_LIMIT.max}."]}
        _validate_range_limit(CepSettings.ENERGY_RATE_LIMIT.min, value,
                              CepSettings.ENERGY_RATE_LIMIT.max, error_message)


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
            error_message = \
                {"misconfiguration": [f"max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            _validate_range_limit(CepSettings.MAX_POWER_KW_LIMIT.min,
                                  kwargs["max_available_power_kW"],
                                  CepSettings.MAX_POWER_KW_LIMIT.max,
                                  error_message)
        elif isinstance(kwargs["max_available_power_kW"], dict):
            error_message = \
                {"misconfiguration": [f"max_available_power_kW should be in between "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.min} & "
                                      f"{CepSettings.MAX_POWER_KW_LIMIT.max}."]}
            for date, value in kwargs["max_available_power_kW"].items():
                _validate_range_limit(CepSettings.MAX_POWER_KW_LIMIT.min, value,
                                      CepSettings.MAX_POWER_KW_LIMIT.max, error_message)
        else:
            raise D3ADeviceException({"misconfiguration": [f"max_available_power_kW has an "
                                                           f"invalid type. "]})

    validate_commercial_producer(**kwargs)


def _validate_range_limit(initial_limit, value, final_limit, error_message):
    if not initial_limit <= value <= final_limit:
        raise D3ADeviceException(error_message)
