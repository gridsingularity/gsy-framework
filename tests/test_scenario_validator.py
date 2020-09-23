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
# flake8: noqa
import unittest
from parameterized import parameterized
import json
from jsonschema import ValidationError
from d3a_interface.scenario_validators import scenario_validator


class TestValidateGlobalSettings(unittest.TestCase):

    @parameterized.expand([("CommercialProducer", "WrongCommercialProducer",),
                           ("FiniteDieselGenerator", "WrongDieselGenerator",),
                           ("PV", "WrongPV",),
                           ("PredefinedPV", "Predef",),
                           ("Load", "LoadWrong",),
                           ("Storage", "StorWrongage",)])
    def test_type_checking_succeeds_for_device_types(self, correct_type, wrong_type):
        scenario = '''{"name": "Area", "type": "Area", "uuid": "a4b42c3c-edc4-4eb3-992b-b6c1c6aae118", "children": [{"name": "device", "risk": 50, "type": "''' + correct_type + '''"}]}'''
        scenario_validator(json.loads(scenario))
        wrong_scenario = '''{"name": "Area", "type": "Area", "uuid": "a4b42c3c-edc4-4eb3-992b-b6c1c6aae118", "children": [{"name": "device", "risk": 50, "type": "''' + wrong_type + '''"}]}'''
        self.assertRaises(ValidationError, scenario_validator, json.loads(wrong_scenario))

    def test_initial_selling_rate_accepts_null_values_for_all_strategies(self):
        scenario = '''
        {"name": "Area", "type": "Area", "uuid": "a4b42c3c-edc4-4eb3-992b-b6c1c6aae118", "children": [ 
            {"name": "PV", "risk": 50, "type": "PV", "uuid": "2c53cf13-a209-4b08-b320-28fad72c8930", "panel_count": 1, "min_selling_rate": 0.0, "number_of_clones": 1, "initial_pv_rate_option": 2, "energy_rate_decrease_option": 1, "power_profile": null, "initial_selling_rate": null}, 
            {"name": "Storage", "risk": 50, "type": "Storage", "uuid": "eec7e801-0959-4072-99b1-41ee1d607e1d", "battery_capacity": 5.0, "break_even_lower": 25.0, "break_even_upper": 25.1, "initial_capacity": 1.0, "number_of_clones": 1, "initial_rate_option": 2, "max_abs_battery_power": 5.0, "energy_rate_decrease_option": 1, "initial_selling_rate": null} 
        ]}'''
        scenario_validator(json.loads(scenario))

    def test_global_settings(self):

        scenario =  '{"name": "Area", "type": "Area", "uuid": "a4b42c3c-edc4-4eb3-992b-b6c1c6aae118", ' \
                    '"children": [ {"name": "PV", "risk": 50, "type": "PV", "uuid": "2c53cf13-a209-4b08-b320-28fad72c8930", "panel_count": 1, "min_selling_rate": 0.0, "number_of_clones": 1, "initial_pv_rate_option": 2, "energy_rate_decrease_option": 1, "power_profile": null, "initial_selling_rate": null}, ' \
                    '{"name": "Load", "type": "Load", "uuid": "cf9cd39b-f127-40c4-a9f5-465c509ca3c4", "hrs_of_day": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17], "avg_power_W": 100, "hrs_per_day": 9, "number_of_clones": 1, "acceptable_energy_rate": 31, "daily_load_profile": null}, ' \
                    '{"name": "Storage", "risk": 50, "type": "Storage", "uuid": "eec7e801-0959-4072-99b1-41ee1d607e1d", "battery_capacity": 5.0, "break_even_lower": 25.0, "break_even_upper": 25.1, "initial_capacity": 1.0, "number_of_clones": 1, "initial_rate_option": 2, "max_abs_battery_power": 5.0, "energy_rate_decrease_option": 1}, ' \
                    '{"name": "Infinite power plant", "type": "CommercialProducer", "uuid": "aa56fe33-a5f4-4a09-8e98-a70d4c931ec4", "number_of_clones": 1}, ' \
                    '{"name": "Finite power plant", "type": "FiniteDieselGenerator", "uuid": "50cd0893-0ac3-42cd-a90a-8e949910fdd4", "energy_rate": 30.0, "number_of_clones": 1, "max_available_power_kW": 1000.0}], "number_of_clones": 1}'
        scenario_validator(json.loads(scenario))

        scenario =  '{"name": "Area", "type": "Area", "uuid": "a4b42c3c-edc4-4eb3-992b-b6c1c6aae118", ' \
                    '"children": [ {"name": "PV", "risk": 50, "type": "PV", "uuid": "2c53cf13-a209-4b08-b320-28fad72c8930", "panel_count": 1, "min_selling_rate": 0.0, "number_of_clones": 1, "initial_pv_rate_option": 2, "energy_rate_decrease_option": 1, "power_profile": null}, ' \
                    '{"name": "Load", "type": "Load", "uuid": "cf9cd39b-f127-40c4-a9f5-465c509ca3c4", "hrs_of_day": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17], "avg_power_W": 100, "hrs_per_day": 9, "number_of_clones": 1, "acceptable_energy_rate": 31, "daily_load_profile": null}, ' \
                    '{"name": "Storage", "risk": 50, "type": "Storage", "uuid": "eec7e801-0959-4072-99b1-41ee1d607e1d", "battery_capacity": 5.0, "break_even_lower": 25.0, "break_even_upper": 25.1, "initial_capacity": 1.0, "number_of_clones": 1, "initial_rate_option": 2, "max_abs_battery_power": 5.0, "energy_rate_decrease_option": 1}, ' \
                    '{"name": "Infinite power plant", "type": "CommercialProducer", "uuid": "aa56fe33-a5f4-4a09-8e98-a70d4c931ec4", "number_of_clones": 1}, ' \
                    '{"name": "Finite power plant", "type": "FiniteDieselGenerator", "uuid": 1, "energy_rate": 30.0, "number_of_clones": 1, "max_available_power_kW": 1000.0}], "number_of_clones": 1}'
        self.assertRaises(ValidationError, scenario_validator, json.loads(scenario))

        scenario = '{"name": 1, "numberOfClones": 10, "children": [' \
                   '{"name": "Load", "type": "Load", "avgPowerW": 200} ]}'
        self.assertRaises(ValidationError, scenario_validator, json.loads(scenario))
        scenario = '{"name": 1, "numberOfClones": 10, "children": [' \
                   '{"name": "battery", "type": "Storage", "batteryCapacity": 1.2, "initialCharge": 90}, ' \
                   '{"name": "battery_plant","type": "Storage", "batteryCapacity": 1.2, "initialCapacity": 0.6}, ' \
                   '{"name": "Load", "type": "Load", "avgPowerW": 200} ]}'
        self.assertRaises(ValidationError, scenario_validator, json.loads(scenario))