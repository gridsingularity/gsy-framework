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
from gsy_framework.validators import utils
from gsy_framework.validators.base_validator import BaseValidator

GeneralSettings = ConstSettings.GeneralSettings
StorageSettings = ConstSettings.StorageSettings


class StorageValidator(BaseValidator):
    """Validator class for Storage devices."""

    @classmethod
    def validate(cls, **kwargs):
        """Validate energy and rate values and the loss function configuration of the device."""
        cls.validate_energy(**kwargs)
        cls.validate_rate(**kwargs)
        cls._validate_loss_function(**kwargs)

    @classmethod
    def validate_energy(cls, **kwargs):
        """Validate energy values of the device."""
        if kwargs.get("initial_soc") is not None:
            error_message = {"misconfiguration": [
                "initial_soc should be in between "
                f"{StorageSettings.INITIAL_CHARGE_LIMIT.min} & "
                f"{StorageSettings.INITIAL_CHARGE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.INITIAL_CHARGE_LIMIT.min,
                kwargs["initial_soc"],
                StorageSettings.INITIAL_CHARGE_LIMIT.max, error_message)

        if kwargs.get("min_allowed_soc") is not None:
            error_message = {"misconfiguration": [
                "min_allowed_soc should be in between "
                f"{StorageSettings.MIN_SOC_LIMIT.min} & "
                f"{StorageSettings.MIN_SOC_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.MIN_SOC_LIMIT.min,
                kwargs["min_allowed_soc"],
                StorageSettings.MIN_SOC_LIMIT.max, error_message)

        if (
                kwargs.get("initial_soc") is not None and kwargs.get("min_allowed_soc") is not None
                and kwargs["initial_soc"] < kwargs["min_allowed_soc"]):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "initial_soc should be greater than or equal to min_allowed_soc."]})

        if kwargs.get("battery_capacity_kWh") is not None:
            error_message = {"misconfiguration": [
                "battery_capacity_kWh should be in between "
                f"{StorageSettings.CAPACITY_LIMIT.min} & "
                f"{StorageSettings.CAPACITY_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.CAPACITY_LIMIT.min,
                kwargs["battery_capacity_kWh"],
                StorageSettings.CAPACITY_LIMIT.max, error_message)

        if kwargs.get("max_abs_battery_power_kW") is not None:
            error_message = {"misconfiguration": [
                "max_abs_battery_power_kW should be in between "
                f"{StorageSettings.MAX_ABS_POWER_RANGE.initial} & "
                f"{StorageSettings.MAX_ABS_POWER_RANGE.final}."]}
            utils.validate_range_limit(
                StorageSettings.MAX_ABS_POWER_RANGE.initial,
                kwargs["max_abs_battery_power_kW"],
                StorageSettings.MAX_ABS_POWER_RANGE.final, error_message)

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate rates of the device."""
        if kwargs.get("initial_selling_rate") is not None:
            error_message = {"misconfiguration": [
                "initial_selling_rate should be in between "
                f"{StorageSettings.INITIAL_SELLING_RATE_LIMIT.min} & "
                f"{StorageSettings.INITIAL_SELLING_RATE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.INITIAL_SELLING_RATE_LIMIT.min,
                kwargs["initial_selling_rate"],
                StorageSettings.INITIAL_SELLING_RATE_LIMIT.max, error_message)

        if kwargs.get("final_selling_rate") is not None:
            error_message = {"misconfiguration": [
                "final_selling_rate should be in between "
                f"{StorageSettings.FINAL_SELLING_RATE_LIMIT.min} & "
                f"{StorageSettings.FINAL_SELLING_RATE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.FINAL_SELLING_RATE_LIMIT.min,
                kwargs["final_selling_rate"],
                StorageSettings.FINAL_SELLING_RATE_LIMIT.max, error_message)

        if (
                kwargs.get("initial_selling_rate") is not None
                and kwargs.get("final_selling_rate") is not None
                and kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
            raise GSyDeviceException(
                {"misconfiguration": ["initial_selling_rate should be greater than or equal to "
                                      "final_selling_rate."]})

        if kwargs.get("initial_buying_rate") is not None:
            error_message = {"misconfiguration": [
                "initial_buying_rate should be in between "
                f"{StorageSettings.INITIAL_BUYING_RATE_LIMIT.min} & "
                f"{StorageSettings.INITIAL_BUYING_RATE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.INITIAL_BUYING_RATE_LIMIT.min,
                kwargs["initial_buying_rate"],
                StorageSettings.INITIAL_BUYING_RATE_LIMIT.max, error_message)

        if kwargs.get("final_buying_rate") is not None:
            error_message = {"misconfiguration": [
                "final_buying_rate should be in between "
                f"{StorageSettings.FINAL_BUYING_RATE_LIMIT.min} & "
                f"{StorageSettings.FINAL_BUYING_RATE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.FINAL_BUYING_RATE_LIMIT.min,
                kwargs["final_buying_rate"],
                StorageSettings.FINAL_BUYING_RATE_LIMIT.max, error_message)

        if (
                kwargs.get("initial_buying_rate") is not None
                and kwargs.get("final_buying_rate") is not None
                and kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "initial_buying_rate should be less than or equal to final_buying_rate."]})

        if (
                kwargs.get("final_selling_rate") is not None
                and kwargs.get("final_buying_rate") is not None
                and kwargs["final_buying_rate"] > kwargs["final_selling_rate"]):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "final_buying_rate should be less than or equal to final_selling_rate."]})

        if kwargs.get("energy_rate_increase_per_update") is not None:
            error_message = {"misconfiguration": [
                "energy_rate_increase_per_update should be in between "
                f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
            utils.validate_range_limit(
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                kwargs["energy_rate_increase_per_update"],
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

        if kwargs.get("energy_rate_decrease_per_update") is not None:
            error_message = {"misconfiguration": [
                "energy_rate_decrease_per_update should be in between "
                f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}
            utils.validate_range_limit(
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                kwargs["energy_rate_decrease_per_update"],
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

        utils.validate_fit_to_limit(
            fit_to_limit=kwargs.get("fit_to_limit"),
            energy_rate_increase_per_update=kwargs.get("energy_rate_increase_per_update"),
            energy_rate_decrease_per_update=kwargs.get("energy_rate_decrease_per_update"))

    @staticmethod
    def _validate_loss_function(**kwargs):
        if kwargs.get("loss_function") is None:
            return

        error_message = {"misconfiguration": [
            "loss_function should either be "
            f"{StorageSettings.LOSS_FUNCTION_LIMIT.min} or "
            f"{StorageSettings.LOSS_FUNCTION_LIMIT.max}."]}
        utils.validate_range_limit(
            StorageSettings.LOSS_FUNCTION_LIMIT.min, kwargs["loss_function"],
            StorageSettings.LOSS_FUNCTION_LIMIT.max, error_message)

        if kwargs.get("loss_per_hour") is None:
            return

        if kwargs["loss_function"] == 1:
            error_message = {
                "misconfiguration": [
                    "loss_per_hour should be in between "
                    f"{StorageSettings.LOSS_PER_HOUR_RELATIVE_LIMIT.min} & "
                    f"{StorageSettings.LOSS_PER_HOUR_RELATIVE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.LOSS_PER_HOUR_RELATIVE_LIMIT.min,
                kwargs["loss_per_hour"],
                StorageSettings.LOSS_PER_HOUR_RELATIVE_LIMIT.max,
                error_message)
        else:
            error_message = {
                "misconfiguration": [
                    "loss_per_hour should be in between "
                    f"{StorageSettings.LOSS_PER_HOUR_ABSOLUTE_LIMIT.min} & "
                    f"{StorageSettings.LOSS_PER_HOUR_ABSOLUTE_LIMIT.max}."]}
            utils.validate_range_limit(
                StorageSettings.LOSS_PER_HOUR_ABSOLUTE_LIMIT.min,
                kwargs["loss_per_hour"],
                StorageSettings.LOSS_PER_HOUR_ABSOLUTE_LIMIT.max,
                error_message)
