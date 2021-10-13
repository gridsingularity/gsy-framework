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
from d3a_interface.validators.base_validator import BaseValidator
from d3a_interface.validators.utils import validate_range_limit

GeneralSettings = ConstSettings.GeneralSettings
PvSettings = ConstSettings.PVSettings


class PVValidator(BaseValidator):
    """Validator class for PV devices."""

    @classmethod
    def validate(cls, **kwargs):
        """Validate the energy and rate values of the device."""
        cls.validate_energy(**kwargs)
        cls.validate_rate(**kwargs)
        cls.validate_settings(**kwargs)

    @classmethod
    def validate_energy(cls, **kwargs):
        """Validate energy values of the device."""
        if kwargs.get("panel_count") is not None:
            error_message = {
                "misconfiguration": ["PV panel count should be in between "
                                     f"{PvSettings.PANEL_COUNT_LIMIT.min} & "
                                     f"{PvSettings.PANEL_COUNT_LIMIT.max}"]}
            validate_range_limit(PvSettings.PANEL_COUNT_LIMIT.min,
                                 kwargs["panel_count"],
                                 PvSettings.PANEL_COUNT_LIMIT.max, error_message)

        if kwargs.get("capacity_kW") is not None:
            error_message = {
                "misconfiguration": ["capacity_kW should be in between "
                                     f"{PvSettings.CAPACITY_KW_LIMIT.min} & "
                                     f"{PvSettings.CAPACITY_KW_LIMIT.max}"]}
            validate_range_limit(PvSettings.CAPACITY_KW_LIMIT.min,
                                 kwargs["capacity_kW"],
                                 PvSettings.CAPACITY_KW_LIMIT.max, error_message)

        if kwargs.get("max_panel_power_W") is not None:  # deprecated
            error_message = {
                "misconfiguration": ["max_panel_power_W should be in between "
                                     f"{PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.min} & "
                                     f"{PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.max}"]}
            validate_range_limit(PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.min,
                                 kwargs["max_panel_power_W"],
                                 PvSettings.MAX_PANEL_OUTPUT_W_LIMIT.max, error_message)

        if kwargs.get("cloud_coverage") is not None:
            if kwargs["cloud_coverage"] != 4 and kwargs.get("power_profile") is not None:
                raise D3ADeviceException(
                    {"misconfiguration": [
                        "cloud_coverage (if values 0-3) & power_profile can't be set together."]})

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate rates of the device."""
        if kwargs.get("final_selling_rate") is not None:
            error_message = {"misconfiguration": ["final_selling_rate should be in between "
                                                  f"{PvSettings.FINAL_SELLING_RATE_LIMIT.min} & "
                                                  f"{PvSettings.FINAL_SELLING_RATE_LIMIT.max}"]}
            validate_range_limit(PvSettings.FINAL_SELLING_RATE_LIMIT.min,
                                 kwargs["final_selling_rate"],
                                 PvSettings.FINAL_SELLING_RATE_LIMIT.max, error_message)

        if kwargs.get("initial_selling_rate") is not None:
            error_message = {"misconfiguration": ["initial_selling_rate should be in between "
                                                  f"{PvSettings.INITIAL_SELLING_RATE_LIMIT.min} & "
                                                  f"{PvSettings.INITIAL_SELLING_RATE_LIMIT.max}"]}
            validate_range_limit(PvSettings.INITIAL_SELLING_RATE_LIMIT.min,
                                 kwargs["initial_selling_rate"],
                                 PvSettings.INITIAL_SELLING_RATE_LIMIT.max, error_message)

        if (kwargs.get("initial_selling_rate") is not None
                and kwargs.get("final_selling_rate") is not None
                and kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]):
            raise D3ADeviceException(
                {"misconfiguration": [
                    "initial_selling_rate/market_maker_rate should be greater than or equal to "
                    "final_selling_rate. Please adapt the market_maker_rate of the configuration "
                    "or the initial_selling_rate."]})

        if (kwargs.get("fit_to_limit") is True
                and kwargs.get("energy_rate_decrease_per_update") is not None):
            raise D3ADeviceException(
                {"misconfiguration": [
                    "fit_to_limit & energy_rate_decrease_per_update can't be set together."]})
        if (kwargs.get("fit_to_limit") is False
                and kwargs.get("energy_rate_decrease_per_update") is None):
            raise D3ADeviceException(
                {"misconfiguration": [
                    "energy_rate_decrease_per_update must be set if fit_to_limit is False."]})

        if kwargs.get("energy_rate_decrease_per_update") is not None:
            error_message = {
                "misconfiguration": ["energy_rate_decrease_per_update should be in between "
                                     f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min} & "
                                     f"{GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max}"]}
            validate_range_limit(GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.min,
                                 kwargs["energy_rate_decrease_per_update"],
                                 GeneralSettings.RATE_CHANGE_PER_UPDATE_LIMIT.max, error_message)

    @classmethod
    def validate_settings(cls, **kwargs):
        """Validator to catch mis-configured PV parameters"""
        # validate location is provided to work with PV orientations
        if (kwargs.get("geo_tag_location") is None and kwargs.get("tilt") is not None):
            raise D3ADeviceException({"misconfiguration": [
                "Geo-coordinate for PV asset must be provided "
                "to work with PV orientations."]})

        # validate azimuth isn't out of bound
        if kwargs.get("azimuth") is not None and not 0 <= kwargs["azimuth"] <= 360:
            raise D3ADeviceException({"misconfiguration": ["Azimuth could only be in between "
                                                           "0 and 360 degrees."]})

        # validate tilt isn't out of bound
        if kwargs.get("tilt") is not None and not 0 <= kwargs["tilt"] <= 90:
            raise D3ADeviceException({"misconfiguration": ["tilt could only be in between "
                                                           "0 and 90 degrees."]})
