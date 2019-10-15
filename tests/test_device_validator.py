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

        self.assertIsNone(validate_load_device(avg_power_W=100))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(avg_power_W=-1)
        with self.assertRaises(D3ADeviceException):
            validate_load_device(avg_power_W=-1)

        self.assertIsNone(validate_load_device(hrs_per_day=0))
        self.assertIsNone(validate_load_device(hrs_per_day=24))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(hrs_per_day=25)

        self.assertIsNone(validate_load_device(final_buying_rate=0))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(final_buying_rate=-10)

        self.assertIsNone(validate_load_device(initial_buying_rate=0))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(initial_buying_rate=-2)

        self.assertIsNone(validate_load_device(initial_buying_rate=5,
                                               final_buying_rate=10))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(initial_buying_rate=10, final_buying_rate=5)

        self.assertIsNone(validate_load_device(hrs_of_day=[0, 3, 20, 21, 22, 23, 24]))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(hrs_of_day=[20, 21, 22, 23, 24, 25, 26])

        self.assertIsNone(validate_load_device(hrs_of_day=[1, 2, 3, 5, 6, 10],
                                               hrs_per_day=6))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(hrs_of_day=[1, 2, 3, 4, 5, 6], hrs_per_day=10)

        self.assertIsNone(validate_load_device(energy_rate_increase_per_update=0))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(energy_rate_increase_per_update=-1)

        self.assertIsNone(validate_load_device(fit_to_limit=False,
                                               energy_rate_increase_per_update=2))
        with self.assertRaises(D3ADeviceException):
            validate_load_device(fit_to_limit=True,
                                 energy_rate_increase_per_update=2)

    def test_pv_device_setting(self):
        self.assertIsNone(validate_pv_device(panel_count=1))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(panel_count=-1)

        self.assertIsNone(validate_pv_device(final_selling_rate=0))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(final_selling_rate=-1)

        self.assertIsNone(validate_pv_device(initial_selling_rate=0))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(initial_selling_rate=-20)

        self.assertIsNone(validate_pv_device(initial_selling_rate=11,
                                             final_selling_rate=10))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(initial_selling_rate=10,
                               final_selling_rate=11)

        self.assertIsNone(validate_pv_device(fit_to_limit=False,
                                             energy_rate_decrease_per_update=2))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(fit_to_limit=True,
                               energy_rate_decrease_per_update=2)

        self.assertIsNone(validate_pv_device(energy_rate_decrease_per_update=0))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(energy_rate_decrease_per_update=-1)

        self.assertIsNone(validate_pv_device(max_panel_power_W=0))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(max_panel_power_W=-5)

        self.assertIsNone(validate_pv_device(cloud_coverage=4, power_profile=""))
        with self.assertRaises(D3ADeviceException):
            validate_pv_device(cloud_coverage=3, power_profile="")

    def test_storage_device_setting(self):
        self.assertIsNone(validate_storage_device(initial_soc=10))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_soc=5)

        self.assertIsNone(validate_storage_device(min_allowed_soc=10))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(min_allowed_soc=2)

        self.assertIsNone(validate_storage_device(initial_soc=25,
                                                  min_allowed_soc=20))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_soc=15, min_allowed_soc=20)

        self.assertIsNone(validate_storage_device(battery_capacity_kWh=0.5))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(battery_capacity_kWh=-1)

        self.assertIsNone(validate_storage_device(max_abs_battery_power_kW=0.05))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(max_abs_battery_power_kW=-1)

        self.assertIsNone(validate_storage_device(initial_selling_rate=0.01))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_selling_rate=-1)

        self.assertIsNone(validate_storage_device(final_selling_rate=0.01))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(final_selling_rate=-2)

        self.assertIsNone(validate_storage_device(initial_selling_rate=11,
                                                  final_selling_rate=10))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_selling_rate=10,
                                    final_selling_rate=11)

        self.assertIsNone(validate_storage_device(initial_buying_rate=0.1))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_buying_rate=-2)

        self.assertIsNone(validate_storage_device(final_buying_rate=0.1))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(final_buying_rate=-3)

        self.assertIsNone(validate_storage_device(initial_buying_rate=10,
                                                  final_buying_rate=11))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(initial_buying_rate=10,
                                    final_buying_rate=9)

        self.assertIsNone(validate_storage_device(final_buying_rate=14,
                                                  final_selling_rate=15))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(final_buying_rate=15,
                                    final_selling_rate=14)

        self.assertIsNone(validate_storage_device(energy_rate_increase_per_update=0.1))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(energy_rate_increase_per_update=-5)

        self.assertIsNone(validate_storage_device(energy_rate_decrease_per_update=0.1))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(energy_rate_decrease_per_update=-3)

        self.assertIsNone(validate_storage_device(fit_to_limit=False,
                                                  energy_rate_increase_per_update=3))
        self.assertIsNone(validate_storage_device(fit_to_limit=False,
                                                  energy_rate_decrease_per_update=3))
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(fit_to_limit=True,
                                    energy_rate_increase_per_update=3)
        with self.assertRaises(D3ADeviceException):
            validate_storage_device(fit_to_limit=True,
                                    energy_rate_decrease_per_update=3)
