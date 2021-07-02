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
from typing import Optional

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException
from d3a_interface.validators.base_validator import BaseValidator
from d3a_interface.validators.utils import validate_range_limit

GeneralSettings = ConstSettings.GeneralSettings
HomeMeterSettings = ConstSettings.HomeMeterSettings


class HomeMeterValidator(BaseValidator):
    """Validator class for Home Meter devices."""

    @classmethod
    def validate(cls, **kwargs):
        """Validate the rate values of the device."""
        cls.validate_rate(**kwargs)

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate rates of a Home Meter device."""
        cls._validate_fit_to_limit(
            fit_to_limit=kwargs.get("fit_to_limit"),
            energy_rate_increase_per_update=kwargs.get("energy_rate_increase_per_update"),
            energy_rate_decrease_per_update=kwargs.get("energy_rate_decrease_per_update"))
        cls._validate_home_meter_consumption_rates(**kwargs)
        cls._validate_home_meter_production_rates(**kwargs)

    @staticmethod
    def _validate_fit_to_limit(
            fit_to_limit: Optional[bool], energy_rate_increase_per_update: Optional[bool],
            energy_rate_decrease_per_update: Optional[bool]):
        if fit_to_limit is True and (
                energy_rate_decrease_per_update is not None
                or energy_rate_increase_per_update is not None):
            raise D3ADeviceException({
                "misconfiguration": [
                    "fit_to_limit and energy_rate_increase/decrease_per_update can't be set "
                    "together."]})

        if fit_to_limit is False and (
                energy_rate_increase_per_update is None
                or energy_rate_decrease_per_update is None):
            raise D3ADeviceException(
                {"misconfiguration": [
                    "energy_rate_increase/decrease_per_update must be set if fit_to_limit is "
                    "False."]})

    @staticmethod
    def _validate_home_meter_consumption_rates(**kwargs):
        """Validate rates related to the consumption activity of the device."""
        if kwargs.get("final_buying_rate") is not None:
            error_message = {
                "misconfiguration": [
                    "final_buying_rate should be in between "
                    f"{HomeMeterSettings.FINAL_BUYING_RATE_LIMIT.min} & "
                    f"{HomeMeterSettings.FINAL_BUYING_RATE_LIMIT.max}."]}

            validate_range_limit(
                HomeMeterSettings.FINAL_BUYING_RATE_LIMIT.min,
                kwargs["final_buying_rate"],
                HomeMeterSettings.FINAL_BUYING_RATE_LIMIT.max, error_message)

        if kwargs.get("initial_buying_rate") is not None:
            error_message = {
                "misconfiguration": [
                    "initial_buying_rate should be in between "
                    f"{HomeMeterSettings.INITIAL_BUYING_RATE_LIMIT.min} & "
                    f"{HomeMeterSettings.INITIAL_BUYING_RATE_LIMIT.max}"]}

            validate_range_limit(
                HomeMeterSettings.INITIAL_BUYING_RATE_LIMIT.min,
                kwargs["initial_buying_rate"],
                HomeMeterSettings.INITIAL_BUYING_RATE_LIMIT.max, error_message)

        if (kwargs.get("initial_buying_rate") is not None
                and kwargs.get("final_buying_rate") is not None
                and kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]):
            raise D3ADeviceException({
                "misconfiguration": [
                    "initial_buying_rate should be less than or equal to final_buying_rate/"
                    "market_maker_rate. Please adapt the market_maker_rate of the configuration "
                    "or the initial_buying_rate."]})

        if kwargs.get("energy_rate_increase_per_update") is not None:
            error_message = {
                "misconfiguration": [
                    "energy_rate_increase_per_update should be in between "
                    f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                    f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}."]}

            validate_range_limit(
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                kwargs["energy_rate_increase_per_update"],
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

    @staticmethod
    def _validate_home_meter_production_rates(**kwargs):
        """Validate rates related to the production activity of the device."""
        if kwargs.get("final_selling_rate") is not None:
            error_message = {
                "misconfiguration": [
                    "final_selling_rate should be in between "
                    f"{HomeMeterSettings.FINAL_SELLING_RATE_LIMIT.min} & "
                    f"{HomeMeterSettings.FINAL_SELLING_RATE_LIMIT.max}"]}

            validate_range_limit(
                HomeMeterSettings.FINAL_SELLING_RATE_LIMIT.min,
                kwargs["final_selling_rate"],
                HomeMeterSettings.FINAL_SELLING_RATE_LIMIT.max, error_message)

        if kwargs.get("initial_selling_rate") is not None:
            error_message = {
                "misconfiguration": [
                    "initial_selling_rate should be in between "
                    f"{HomeMeterSettings.INITIAL_SELLING_RATE_LIMIT.min} & "
                    f"{HomeMeterSettings.INITIAL_SELLING_RATE_LIMIT.max}"]}

            validate_range_limit(
                HomeMeterSettings.INITIAL_SELLING_RATE_LIMIT.min,
                kwargs["initial_selling_rate"],
                HomeMeterSettings.INITIAL_SELLING_RATE_LIMIT.max, error_message)

        if (kwargs.get("initial_selling_rate") is not None
                and kwargs.get("final_selling_rate") is not None
                and kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
            raise D3ADeviceException(
                {"misconfiguration": [
                    "initial_selling_rate/market_maker_rate should be greater than or equal to "
                    "final_selling_rate. Please adapt the market_maker_rate of the configuration "
                    "or the initial_selling_rate."]})

        if kwargs.get("energy_rate_decrease_per_update") is not None:
            error_message = {
                "misconfiguration": [
                    "energy_rate_decrease_per_update should be in between "
                    f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                    f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}"]}

            validate_range_limit(
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                kwargs["energy_rate_decrease_per_update"],
                GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)
