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
from d3a_interface.validators.utils import validate_range_limit

GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings


def validate_load_device(**kwargs):
    validate_load_device_energy(**kwargs)
    validate_load_device_price(**kwargs)


def validate_load_device_energy(**kwargs):
    if "avg_power_W" in kwargs and kwargs["avg_power_W"] is not None:
        error_message = {"misconfiguration": [f"avg_power_W should be in between "
                                              f"{LoadSettings.AVG_POWER_LIMIT.min} & "
                                              f"{LoadSettings.AVG_POWER_LIMIT.max}."]}
        validate_range_limit(LoadSettings.AVG_POWER_LIMIT.min,
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
        validate_range_limit(LoadSettings.HOURS_LIMIT.min,
                             kwargs["hrs_per_day"],
                             LoadSettings.HOURS_LIMIT.max, error_message)
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
                                  f"greater than or equal hrs_per_day."]})

    if (("avg_power_W" in kwargs and kwargs["avg_power_W"] is not None) or
            ("hrs_per_day" in kwargs and kwargs["hrs_per_day"] is not None) or
            ("hrs_of_day" in kwargs and kwargs["hrs_of_day"] is not None)) and \
            ("daily_load_profile" in kwargs and kwargs["daily_load_profile"] is not None):
        raise D3ADeviceException(
            {"misconfiguration": [f"daily_load_profile and all or one [hrs_per_day, hrs_of_day, "
                                  f"avg_power_W] can't be set together."]})


def validate_load_device_price(**kwargs):
    if "final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None:
        error_message = {"misconfiguration": [f"final_buying_rate should be in between "
                                              f"{LoadSettings.FINAL_BUYING_RATE_LIMIT.min} & "
                                              f"{LoadSettings.FINAL_BUYING_RATE_LIMIT.max}."]}
        validate_range_limit(LoadSettings.FINAL_BUYING_RATE_LIMIT.min,
                             kwargs["final_buying_rate"],
                             LoadSettings.FINAL_BUYING_RATE_LIMIT.max, error_message)
    if "initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None:
        error_message = \
            {"misconfiguration": [f"initial_buying_rate should be in between "
                                  f"{LoadSettings.INITIAL_BUYING_RATE_LIMIT.min} & "
                                  f"{LoadSettings.INITIAL_BUYING_RATE_LIMIT.max}"]}
        validate_range_limit(LoadSettings.INITIAL_BUYING_RATE_LIMIT.min,
                             kwargs["initial_buying_rate"],
                             LoadSettings.INITIAL_BUYING_RATE_LIMIT.max, error_message)

    if ("initial_buying_rate" in kwargs and kwargs["initial_buying_rate"] is not None) and \
            ("final_buying_rate" in kwargs and kwargs["final_buying_rate"] is not None) and \
            (kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
        raise D3ADeviceException({"misconfiguration": [
            "initial_buying_rate should be less than or equal to final_buying_rate/"
            "market_maker_rate. Please adapt the market_maker_rate of the configuration "
            "or the initial_buying_rate."]})
    if "energy_rate_increase_per_update" in kwargs and \
            kwargs["energy_rate_increase_per_update"] is not None:
        error_message = \
            {"misconfiguration": [f"energy_rate_increase_per_update should be in between "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                                  f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
        validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                             kwargs["energy_rate_increase_per_update"],
                             GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

    if (kwargs.get("fit_to_limit") is True
            and kwargs.get("energy_rate_increase_per_update") is not None):
        raise D3ADeviceException(
            {"misconfiguration": [
                "fit_to_limit & energy_rate_increase_per_update can't be set together."]})
    if (kwargs.get("fit_to_limit") is False
            and kwargs.get("energy_rate_increase_per_update") is None):
        raise D3ADeviceException(
            {"misconfiguration": [
                "energy_rate_increase_per_update must be set if fit_to_limit is False."]})
