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
import unittest

from d3a_interface.device_validator import validate_load_device, validate_pv_device, \
    validate_storage_device
from d3a_interface.constants_limits import ConstSettings
from d3a_interface.exceptions import D3ADeviceException

GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings
PvSettings = ConstSettings.PVSettings
StorageSettings = ConstSettings.StorageSettings


class TestValidateDeviceSettings(unittest.TestCase):

    def test_load_device_setting(self):
        with self.assertRaises(D3ADeviceException):
            validate_load_device(avg_power_W=-1)
        with self.assertRaises(D3ADeviceException):
            validate_load_device(avg_power_W=-1)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(hrs_per_day=25)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(final_buying_rate=-10)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(initial_buying_rate=-2)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(initial_buying_rate=10, final_buying_rate=5)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(hrs_of_day=[20, 21, 22, 23, 24, 25, 26])

        with self.assertRaises(D3ADeviceException):
            validate_load_device(hrs_of_day=[1, 2, 3, 4, 5, 6], hrs_per_day=10)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(energy_rate_increase_per_update=-1)

        with self.assertRaises(D3ADeviceException):
            validate_load_device(fit_to_limit=True,
                                 energy_rate_increase_per_update=2)

    def test_pv_device_setting(self):
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(panel_count=-1)

        with self.assertRaises(D3ADeviceException):
            validate_pv_device(final_selling_rate=-1)

        with self.assertRaises(D3ADeviceException):
            validate_pv_device(initial_selling_rate=-20)

        with self.assertRaises(D3ADeviceException):
            validate_pv_device(initial_selling_rate=10,
                               final_selling_rate=11)

        with self.assertRaises(D3ADeviceException):
            validate_pv_device(fit_to_limit=True,
                               energy_rate_decrease_per_update=2)

        with self.assertRaises(D3ADeviceException):
            validate_pv_device(energy_rate_decrease_per_update=-1)

        with self.assertRaises(D3ADeviceException):
            validate_pv_device(max_panel_power_W=-5)

    def test_storage_device_setting(self):
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_soc=5)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(min_allowed_soc=2)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_soc=15, min_allowed_soc=20)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(battery_capacity_kWh=-1)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(max_abs_battery_power_kW=-1)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_selling_rate=-1)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(final_selling_rate=-2)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_selling_rate=10,
                                    final_selling_rate=11)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_buying_rate=-2)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(final_buying_rate=-3)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_buying_rate=10,
                                    final_buying_rate=9)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(final_buying_rate=15,
                                    final_selling_rate=14)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(energy_rate_increase_per_update=-5)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(energy_rate_decrease_per_update=-3)

        with self.assertRaises(D3ADeviceException):
            validate_storage_device(fit_to_limit=True,
                                    energy_rate_increase_per_update=3)
