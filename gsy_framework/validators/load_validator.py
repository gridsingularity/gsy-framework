"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If
not, see <http://www.gnu.org/licenses/>.
"""
from gsy_framework.constants_limits import ConstSettings
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.validators.utils import validate_range_limit

GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings


class LoadValidator(BaseValidator):
    """Validator class for Load devices."""

    @classmethod
    def validate(cls, **kwargs):
        """Validate the energy and rate values of the device."""
        cls.validate_energy(**kwargs)
        cls.validate_rate(**kwargs)

    @classmethod
    def validate_energy(cls, **kwargs):
        """Validate energy values of the device."""
        if kwargs.get("avg_power_W") is not None:
            error_message = {"misconfiguration": ["avg_power_W should be in between "
                                                  f"{LoadSettings.AVG_POWER_LIMIT.min} & "
                                                  f"{LoadSettings.AVG_POWER_LIMIT.max}."]}
            validate_range_limit(LoadSettings.AVG_POWER_LIMIT.min,
                                 kwargs["avg_power_W"],
                                 LoadSettings.AVG_POWER_LIMIT.max, error_message)

        if (kwargs.get("avg_power_W") is not None
                and kwargs.get("daily_load_profile") is not None):
            raise GSyDeviceException(
                {"misconfiguration": ["daily_load_profile shouldn't be set with avg_power_W."]})

        if (kwargs.get("avg_power_W") is not None
                and kwargs.get("daily_load_profile") is not None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "daily_load_profile and avg_power_W can't be set together."]})

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate rates of the device."""
        if kwargs.get("final_buying_rate") is not None:
            error_message = {"misconfiguration": ["final_buying_rate should be in between "
                                                  f"{LoadSettings.FINAL_BUYING_RATE_LIMIT.min} & "
                                                  f"{LoadSettings.FINAL_BUYING_RATE_LIMIT.max}."]}
            validate_range_limit(LoadSettings.FINAL_BUYING_RATE_LIMIT.min,
                                 kwargs["final_buying_rate"],
                                 LoadSettings.FINAL_BUYING_RATE_LIMIT.max, error_message)

        if kwargs.get("initial_buying_rate") is not None:
            error_message = {"misconfiguration": [
                "initial_buying_rate should be in between "
                f"{LoadSettings.INITIAL_BUYING_RATE_LIMIT.min} & "
                f"{LoadSettings.INITIAL_BUYING_RATE_LIMIT.max}"]}
            validate_range_limit(LoadSettings.INITIAL_BUYING_RATE_LIMIT.min,
                                 kwargs["initial_buying_rate"],
                                 LoadSettings.INITIAL_BUYING_RATE_LIMIT.max, error_message)

        if (kwargs.get("initial_buying_rate") is not None
                and kwargs.get("final_buying_rate") is not None
                and kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
            raise GSyDeviceException({"misconfiguration": [
                "initial_buying_rate should be less than or equal to final_buying_rate/"
                "market_maker_rate. Please adapt the market_maker_rate of the configuration "
                "or the initial_buying_rate."]})

        if kwargs.get("energy_rate_increase_per_update") is not None:
            error_message = {"misconfiguration": [
                "energy_rate_increase_per_update should be in between "
                f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
            validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                                 kwargs["energy_rate_increase_per_update"],
                                 GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

        if (kwargs.get("fit_to_limit") is True
                and kwargs.get("energy_rate_increase_per_update") is not None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "fit_to_limit & energy_rate_increase_per_update can't be set together."]})
        if (kwargs.get("fit_to_limit") is False
                and kwargs.get("energy_rate_increase_per_update") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "energy_rate_increase_per_update must be set if fit_to_limit is False."]})
