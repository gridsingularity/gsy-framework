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
import json

from d3a_interface.device_validator import validate_load_device, validate_pv_device, \
    validate_storage_device
from d3a_interface.constants_limits import ConstSettings

GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings
PvSettings = ConstSettings.PVSettings
StorageSettings = ConstSettings.StorageSettings


class TestValidateDeviceSettings(unittest.TestCase):

    def test_load_device_setting(self):
        assert validate_load_device(avg_power_W=-1) == \
               json.dumps({"mis_configuration": [f"avg_power_W should be in between "
                                                 f"{LoadSettings.AVG_POWER_RANGE.min} & "
                                                 f"{LoadSettings.AVG_POWER_RANGE.max}."]})

        assert validate_load_device(hrs_per_day=25) == json.dumps(
            {"mis_configuration": [f"hrs_per_day should be in between "
                                   f"{LoadSettings.HOURS_RANGE.min} & "
                                   f"{LoadSettings.HOURS_RANGE.max}."]})

        assert validate_load_device(final_buying_rate=-10) == json.dumps(
            {"mis_configuration": [f"final_buying_rate should be in between "
                                   f"{LoadSettings.FINAL_BUYING_RATE_RANGE.min} & "
                                   f"{LoadSettings.FINAL_BUYING_RATE_RANGE.max}."]})

        assert validate_load_device(initial_buying_rate=-2) == json.dumps(
            {"mis_configuration": [f"initial_buying_rate should be in between "
                                   f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.min} & "
                                   f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.max}"]})

        assert validate_load_device(initial_buying_rate=10, final_buying_rate=5) == json.dumps(
            {"mis_configuration": [f"initial_buying_rate should be less than "
                                   f"final_buying_rate."]})

        assert validate_load_device(hrs_of_day=[20, 21, 22, 23, 24, 25, 26]) == json.dumps(
            {"mis_configuration": [f"hrs_of_day should be less between "
                                   f"{LoadSettings.HOURS_RANGE.min} & "
                                   f"{LoadSettings.HOURS_RANGE.max}."]})

        assert validate_load_device(hrs_of_day=[1, 2, 3, 4, 5, 6], hrs_per_day=10) == json.dumps(
            {"mis_configuration": [f"length of hrs_of_day list should be "
                                   f"greater than hrs_per_day."]})

        assert validate_load_device(energy_rate_increase_per_update=-1) == json.dumps(
            {"mis_configuration": [f"energy_rate_increase_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})

        assert validate_load_device(fit_to_limit=True,
                                    energy_rate_increase_per_update=2) == json.dumps(
            {"mis_configuration": [f"fit_to_limit & energy_rate_increase_per_update"
                                   f"can't be set together."]})

    def test_pv_device_setting(self):
        assert validate_pv_device(panel_count=-1) == json.dumps(
            {"mis_configuration": [f"PV panel count should be in between "
                                   f"{PvSettings.PANEL_COUNT_RANGE.min} & "
                                   f"{PvSettings.PANEL_COUNT_RANGE.max}"]})

        assert validate_pv_device(final_selling_rate=-1) == json.dumps(
            {"mis_configuration": [f"final_selling_rate should be in between "
                                   f"{PvSettings.MIN_SELL_RATE_RANGE.min} & "
                                   f"{PvSettings.MIN_SELL_RATE_RANGE.max}"]})

        assert validate_pv_device(initial_selling_rate=-20) == json.dumps(
            {"mis_configuration": [f"initial_selling_rate should be in between "
                                   f"{PvSettings.INITIAL_RATE_RANGE.min} & "
                                   f"{PvSettings.INITIAL_RATE_RANGE.max}"]})

        assert validate_pv_device(initial_selling_rate=10,
                                  final_selling_rate=11) == json.dumps(
            {"mis_configuration": [f"initial_selling_rate should be greater"
                                   f"than or equal to final_selling_rate."]})

        assert validate_pv_device(fit_to_limit=True,
                                  energy_rate_decrease_per_update=2) == json.dumps(
            {"mis_configuration": [f"fit_to_limit & energy_rate_decrease_per_update"
                                   f"can't be set together."]})

        assert validate_pv_device(energy_rate_decrease_per_update=-1) == json.dumps(
            {"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}"]})

        assert validate_pv_device(max_panel_power_W=-5) == json.dumps(
            {"mis_configuration": [f"max_panel_power_W should be in between "
                                   f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.min} & "
                                   f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.max}"]})

    def test_storage_device_setting(self):
        assert validate_storage_device(initial_soc=5) == json.dumps(
            {"mis_configuration": [f"initial_soc should be in between "
                                   f"{StorageSettings.INITIAL_CHARGE_RANGE.min} & "
                                   f"{StorageSettings.INITIAL_CHARGE_RANGE.max}."]})

        assert validate_storage_device(min_allowed_soc=2) == json.dumps(
            {"mis_configuration": [f"min_allowed_soc should be in between "
                                   f"{StorageSettings.MIN_SOC_RANGE.min} & "
                                   f"{StorageSettings.MIN_SOC_RANGE.max}."]})

        assert validate_storage_device(initial_soc=15, min_allowed_soc=20) == json.dumps(
            {"mis_configuration": [f"initial_soc should be greater"
                                   f"than or equal to min_allowed_soc."]})

        assert validate_storage_device(battery_capacity_kWh=-1) == json.dumps(
            {"mis_configuration": [f"battery_capacity_kWh should be in between "
                                   f"{StorageSettings.CAPACITY_RANGE.min} & "
                                   f"{StorageSettings.CAPACITY_RANGE.max}."]})

        assert validate_storage_device(max_abs_battery_power_kW=-1) == json.dumps(
            {"mis_configuration": [f"max_abs_battery_power_kW should be in between "
                                   f"{StorageSettings.MAX_ABS_POWER_RANGE.min} & "
                                   f"{StorageSettings.MAX_ABS_POWER_RANGE.max}."]})

        assert validate_storage_device(initial_selling_rate=-1) == json.dumps(
            {"mis_configuration": [f"initial_selling_rate should be in between "
                                   f"{StorageSettings.INITIAL_SELLING_RANGE.min} & "
                                   f"{StorageSettings.INITIAL_SELLING_RANGE.max}."]})

        assert validate_storage_device(final_selling_rate=-2) == json.dumps(
            {"mis_configuration": [f"final_selling_rate should be in between "
                                   f"{StorageSettings.FINAL_SELLING_RANGE.min} & "
                                   f"{StorageSettings.FINAL_SELLING_RANGE.max}."]})

        assert validate_storage_device(initial_selling_rate=10,
                                       final_selling_rate=11) == json.dumps(
            {"mis_configuration": [f"initial_selling_rate should be greater"
                                   f"than or equal to final_selling_rate."]})

        assert validate_storage_device(initial_buying_rate=-2) == json.dumps(
            {"mis_configuration": [f"initial_buying_rate should be in between "
                                   f"{StorageSettings.INITIAL_BUYING_RANGE.min} & "
                                   f"{StorageSettings.INITIAL_BUYING_RANGE.max}."]})
        assert validate_storage_device(final_buying_rate=-3) == json.dumps(
            {"mis_configuration": [f"final_buying_rate should be in between "
                                   f"{StorageSettings.FINAL_BUYING_RANGE.min} & "
                                   f"{StorageSettings.FINAL_BUYING_RANGE.max}."]})

        assert validate_storage_device(initial_buying_rate=10,
                                       final_buying_rate=9) == json.dumps(
            {"mis_configuration": [f"initial_buying_rate should be less "
                                   f"than or equal to final_buying_rate."]})

        assert validate_storage_device(final_buying_rate=15,
                                       final_selling_rate=14) == json.dumps(
            {"mis_configuration": [f"final_buying_rate should be less "
                                   f"than or equal to final_selling_rate."]})

        assert validate_storage_device(energy_rate_increase_per_update=-5) == json.dumps(
            {"mis_configuration": [f"energy_rate_increase_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})

        assert validate_storage_device(energy_rate_decrease_per_update=-3) == json.dumps(
            {"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
                                   f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})

        assert validate_storage_device(fit_to_limit=True,
                                       energy_rate_increase_per_update=3) == json.dumps(
            {"mis_configuration": [f"fit_to_limit & energy_rate_change_per_update "
                                   f"can't be set together."]})
