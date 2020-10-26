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
from pendulum import duration
from datetime import timedelta
from d3a_interface.settings_validators import validate_global_settings
from d3a_interface.exceptions import D3ASettingsException
from d3a_interface.constants_limits import ConstSettings


class TestValidateGlobalSettings(unittest.TestCase):

    def test_wrong_market_count(self):
        self.assertRaises(D3ASettingsException, validate_global_settings, {"market_count": 0})

    def test_wrong_tick_and_slot_lengths(self):
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"tick_length": duration(seconds=15),
                           "slot_length": duration(seconds=15) *
                           (ConstSettings.GeneralSettings.MIN_NUM_TICKS - 1)})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"slot_length": duration(
                              minutes=ConstSettings.GeneralSettings.MAX_SLOT_LENGTH_M + 1)})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"tick_length": duration(minutes=15) /
                           (ConstSettings.GeneralSettings.MIN_NUM_TICKS - 1),
                           "slot_length": duration(minutes=15)})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"tick_length": duration(minutes=16),
                           "slot_length": duration(minutes=15)})
        # test for integer input
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"tick_length": 16 * 60, "slot_length": 15})
        # test for timedelta
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"tick_length": timedelta(minutes=16),
                           "slot_length": timedelta(minutes=15)})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"slot_length": duration(minutes=1)})

        validate_global_settings({"tick_length": duration(seconds=10),
                                  "slot_length": duration(
                                    minutes=ConstSettings.GeneralSettings.MIN_SLOT_LENGTH_M)})

    def test_wrong_sim_duration(self):
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"slot_length": duration(minutes=15),
                           "sim_duration": duration(minutes=14)})

    def test_wrong_spot_market_type(self):
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"spot_market_type": ConstSettings.IAASettings.MARKET_TYPE_LIMIT[0] - 1})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"spot_market_type": ConstSettings.IAASettings.MARKET_TYPE_LIMIT[1] + 1})

    def test_wrong_cloud_coverage(self):
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"cloud_coverage": ConstSettings.PVSettings.CLOUD_COVERAGE_LIMIT[0] - 1})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"cloud_coverage": ConstSettings.PVSettings.CLOUD_COVERAGE_LIMIT[1] + 1})

    def test_wrong_max_panel_power_W(self):
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"max_panel_power_W":
                           ConstSettings.PVSettings.MAX_PANEL_OUTPUT_W_LIMIT[0] - 1})
        self.assertRaises(D3ASettingsException, validate_global_settings,
                          {"max_panel_power_W":
                           ConstSettings.PVSettings.MAX_PANEL_OUTPUT_W_LIMIT[1] + 1})

    def test_wrong_grid_fee_type(self):
        validate_global_settings({"grid_fee_type": 1})
        self.assertRaises(D3ASettingsException, validate_global_settings, {"grid_fee_type": 0})
        self.assertRaises(D3ASettingsException, validate_global_settings, {"grid_fee_type": 3})
