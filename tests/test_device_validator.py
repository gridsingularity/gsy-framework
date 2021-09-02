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
from unittest.mock import patch
from uuid import uuid4

import pytest

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException
from d3a_interface.validators import (
    SmartMeterValidator, LoadValidator, PVValidator, StorageValidator, CommercialProducerValidator,
    InfiniteBusValidator, MarketMakerValidator, FiniteDieselGeneratorValidator)

GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings
PvSettings = ConstSettings.PVSettings
StorageSettings = ConstSettings.StorageSettings


VALID_LOAD_PROFILE = {"1": 3, "10": 4.2, "22:00": 0.1}


class TestValidateDeviceSettings:
    """Test the validation of the devices."""

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"avg_power_W": 100},
        {"hrs_per_day": 0},
        {"hrs_per_day": 24},
        {"final_buying_rate": 0},
        {"initial_buying_rate": 0},
        {"initial_buying_rate": 5, "final_buying_rate": 10},
        {"hrs_of_day": [0, 3, 20, 21, 22, 23, 24]},
        {"hrs_of_day": [1, 2, 3, 5, 6, 10], "hrs_per_day": 6},
        {"energy_rate_increase_per_update": 0},
        {"fit_to_limit": False, "energy_rate_increase_per_update": 2},
        {"fit_to_limit": True, "energy_rate_increase_per_update": None},
        {"daily_load_profile": VALID_LOAD_PROFILE}
    ])
    def test_load_device_setting_succeeds(valid_arguments):
        """The load device validation succeeds when valid arguments are provided."""
        assert LoadValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"avg_power_W": -1},
        {"hrs_per_day": 25},
        {"final_buying_rate": -10},
        {"initial_buying_rate": -2},
        {"initial_buying_rate": 10, "final_buying_rate": 5},
        {"hrs_of_day": [20, 21, 22, 23, 24, 25, 26]},
        {"hrs_of_day": [1, 2, 3, 4, 5, 6], "hrs_per_day": 10},
        {"energy_rate_increase_per_update": -1},
        {"avg_power_W": 100, "daily_load_profile": VALID_LOAD_PROFILE},
        {"hrs_per_day": 1, "daily_load_profile": VALID_LOAD_PROFILE},
        {"hrs_of_day": [1, 2, 3, 4, 5, 6], "daily_load_profile": VALID_LOAD_PROFILE},
        {"fit_to_limit": True, "energy_rate_increase_per_update": 2},
        {"fit_to_limit": False, "energy_rate_increase_per_update": None},
    ])
    def test_load_device_setting_fails(failing_arguments):
        """The load device validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            LoadValidator.validate(**failing_arguments)

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"panel_count": 1},
        {"final_selling_rate": 0},
        {"initial_selling_rate": 0},
        {"initial_selling_rate": 11, "final_selling_rate": 10},
        {"fit_to_limit": False, "energy_rate_decrease_per_update": 2},
        {"fit_to_limit": True, "energy_rate_decrease_per_update": None},
        {"energy_rate_decrease_per_update": 0},
        {"capacity_kW": 0},
        {"max_panel_power_W": 0},
        {"cloud_coverage": 4, "power_profile": ""}
    ])
    def test_pv_device_setting_succeeds(valid_arguments):
        """The PV device validation succeeds when valid arguments are provided."""
        assert PVValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"panel_count": -1},
        {"final_selling_rate": -1},
        {"initial_selling_rate": -20},
        {"initial_selling_rate": 10, "final_selling_rate": 11},
        {"fit_to_limit": True, "energy_rate_decrease_per_update": 2},
        {"fit_to_limit": False, "energy_rate_decrease_per_update": None},
        {"energy_rate_decrease_per_update": -1},
        {"capacity_kW": -5},
        {"max_panel_power_W": -5},
        {"cloud_coverage": 3, "power_profile": ""},
        {"cloud_coverage": 2, "power_profile": ""}
    ])
    def test_pv_device_setting_fails(failing_arguments):
        """The PV device validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            PVValidator.validate(**failing_arguments)

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"initial_soc": 10},
        {"min_allowed_soc": 10},
        {"initial_soc": 25, "min_allowed_soc": 20},
        {"battery_capacity_kWh": 0.5},
        {"max_abs_battery_power_kW": 0.05},
        {"initial_selling_rate": 0.01},
        {"final_selling_rate": 0.01},
        {"initial_selling_rate": 11, "final_selling_rate": 10},
        {"initial_buying_rate": 0.1},
        {"final_buying_rate": 0.1},
        {"initial_buying_rate": 10, "final_buying_rate": 11},
        {"final_buying_rate": 14, "final_selling_rate": 15},
        {"energy_rate_increase_per_update": 0.1},
        {"energy_rate_decrease_per_update": 0.1},
        {"fit_to_limit": False, "energy_rate_increase_per_update": 3,
         "energy_rate_decrease_per_update": 3},
        {"fit_to_limit": False, "energy_rate_decrease_per_update": 3,
         "energy_rate_increase_per_update": 3},
        {"loss_function": 1, "loss_per_hour": 1},
        {"loss_function": 2, "loss_per_hour": 300},
    ])
    def test_storage_device_setting_succeeds(valid_arguments):
        """The storage device validation succeeds when correct arguments are provided."""
        assert StorageValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"initial_soc": -0.001},
        {"min_allowed_soc": -0.001},
        {"initial_soc": 15, "min_allowed_soc": 20},
        {"battery_capacity_kWh": -1},
        {"max_abs_battery_power_kW": -1},
        {"initial_selling_rate": -1},
        {"final_selling_rate": -2},
        {"initial_selling_rate": 10, "final_selling_rate": 11},
        {"initial_buying_rate": -2},
        {"final_buying_rate": -3},
        {"initial_buying_rate": 10, "final_buying_rate": 9},
        {"final_buying_rate": 15, "final_selling_rate": 14},
        {"energy_rate_increase_per_update": -5},
        {"energy_rate_decrease_per_update": -3},
        {"fit_to_limit": True, "energy_rate_increase_per_update": 3},
        {"fit_to_limit": True, "energy_rate_decrease_per_update": 3},
        {"fit_to_limit": False, "energy_rate_increase_per_update": 3},
        {"fit_to_limit": False, "energy_rate_decrease_per_update": 3},
        {"loss_function": 1, "loss_per_hour": 2},
        {"loss_function": 1, "loss_per_hour": -1},
        {"loss_function": 2, "loss_per_hour": 10001},
        {"loss_function": 2, "loss_per_hour": -1},
    ])
    def test_storage_device_setting_fails(failing_arguments):
        """The storage validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            StorageValidator.validate(**failing_arguments)

    @staticmethod
    def test_commercial_producer_setting():
        """The commercial producer validation succeeds when correct arguments are provided."""
        assert CommercialProducerValidator.validate(energy_rate=10) is None

    @staticmethod
    def test_commercial_producer_setting_fails():
        """The commercial producer validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            CommercialProducerValidator.validate(energy_rate=-5)

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"energy_rate_profile": str({"0": "30", "2": "33"}),
         "energy_rate_profile_uuid": str(uuid4())},
        {"energy_rate_profile": str({"0": "30", "2": "33"}),
         "energy_rate_profile_uuid": str(uuid4()), "grid_connected": True},
        {"energy_rate": str({"0": 30, "2": 33})},
        {"energy_rate": 35}
    ])
    def test_market_maker_setting_succeeds(valid_arguments):
        """The market maker validation succeeds when correct arguments are provided."""
        assert MarketMakerValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"energy_rate_profile": 30},
        {"energy_rate": -5},
        {"energy_rate_profile": str({"0": 30, "2": 33})},
        {"energy_rate": str({"0": -30, "2": 33})},
        {"grid_connected": 30}
    ])
    def test_market_maker_setting_fails(failing_arguments):
        """The market maker validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            MarketMakerValidator.validate(**failing_arguments)

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"energy_rate_profile": str({"0": "30", "2": "33"}),
         "energy_rate_profile_uuid": str(uuid4())},
        {"energy_rate_profile": str({"0": "30", "2": "33"}),
         "energy_rate_profile_uuid": str(uuid4()),
         "buying_rate_profile": str({"0": "29", "2": "28"}),
         "buying_rate_profile_uuid": str(uuid4())},
        {"energy_rate": str({"0": 30, "2": 33})},
        {"energy_rate": 35}
    ])
    def test_infinite_bus_setting_succeeds(valid_arguments):
        """The infinite bus validation succeeds when correct arguments are provided."""
        assert InfiniteBusValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"energy_rate_profile": 30},
        {"energy_rate": -5},
        {"energy_rate_profile": str({"0": 30, "2": 33})},
        {"energy_rate": str({"0": -30, "2": 33})},
        {"buying_rate_profile": str({"0": "29", "2": "28"})},
        {"buying_rate_profile_uuid": uuid4()}
    ])
    def test_infinite_bus_setting_fails(failing_arguments):
        """The infinite bus validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            InfiniteBusValidator.validate(**failing_arguments)

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"max_available_power_kW": 1},
        {"energy_rate": 1},
        {"energy_rate": 100}
    ])
    def test_finite_diesel_generator_succeeds(valid_arguments):
        """The FiniteDiesel validation succeeds when correct arguments are provided."""
        assert FiniteDieselGeneratorValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"max_available_power_kW": -1},
        {"energy_rate": -1}])
    def test_finite_diesel_generator_fails(failing_arguments):
        """The FiniteDiesel validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            FiniteDieselGeneratorValidator.validate(**failing_arguments)


class TestSmartMeterValidator:
    """Tests for the SmartMeterValidator class."""

    @staticmethod
    @patch.object(SmartMeterValidator, "validate_rate")
    def test_validate(validate_price_mock):
        """The validate method correctly calls the individual validation methods."""
        SmartMeterValidator.validate()
        validate_price_mock.assert_called_once_with()

    @staticmethod
    @pytest.mark.parametrize("valid_arguments", [
        {"initial_buying_rate": 10, "final_buying_rate": 13, "energy_rate_increase_per_update": 1,
         "initial_selling_rate": 13, "final_selling_rate": 10,
         "energy_rate_decrease_per_update": 2},
        {"fit_to_limit": False, "energy_rate_increase_per_update": 1,
         "energy_rate_decrease_per_update": 1},
        {"fit_to_limit": False, "energy_rate_decrease_per_update": 1,
         "energy_rate_increase_per_update": 1},
    ])
    def test_validate_price_succeeds(valid_arguments):
        """The validation succeeds when valid arguments are provided."""
        assert SmartMeterValidator.validate(**valid_arguments) is None

    @staticmethod
    @pytest.mark.parametrize("failing_arguments", [
        {"initial_buying_rate": 15, "final_buying_rate": 13},
        {"initial_selling_rate": 10, "final_selling_rate": 13},
        {"fit_to_limit": True, "energy_rate_increase_per_update": 1},
        {"fit_to_limit": True, "energy_rate_decrease_per_update": 1},
        {"fit_to_limit": False, "energy_rate_increase_per_update": 1},
        {"fit_to_limit": False, "energy_rate_decrease_per_update": 1},
    ])
    def test_validate_price_fails(failing_arguments):
        """The validation fails when incompatible arguments are provided."""
        with pytest.raises(D3ADeviceException):
            SmartMeterValidator.validate_rate(**failing_arguments)
