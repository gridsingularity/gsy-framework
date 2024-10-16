"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

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

from gsy_framework.exceptions import GSyDeviceException, GSyAreaException
from gsy_framework.area_validator import validate_area


class TestValidateAreaSettings(unittest.TestCase):

    def test_area_setting(self):
        self.assertIsNone(validate_area())
        self.assertIsNone(validate_area(grid_fee_constant=0))
        with self.assertRaises(GSyDeviceException):
            validate_area(grid_fee_constant=-1)
        with self.assertRaises(GSyAreaException):
            validate_area(baseline_peak_energy_import_kWh=-1.0)
        with self.assertRaises(GSyAreaException):
            validate_area(baseline_peak_energy_export_kWh=-1.0)
        with self.assertRaises(GSyAreaException):
            validate_area(import_capacity_kVA=-1.0)
        with self.assertRaises(GSyAreaException):
            validate_area(export_capacity_kVA=-1.0)
