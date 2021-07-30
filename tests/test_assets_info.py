import unittest
from uuid import uuid4
from d3a_interface.sim_results.simulation_assets_info import SimulationAssetsInfo


class TestSimulationAssetsInfo(unittest.TestCase):

    def setUp(self):
        self.assets_info = SimulationAssetsInfo()

    def tearDown(self):
        pass

    def test_update(self):
        core_stats = {
            str(uuid4()): {
                "total_energy_demanded_wh": 10,
            },
            str(uuid4()): {
                "total_energy_demanded_wh": 20,
            },
            str(uuid4()): {
                "total_energy_demanded_wh": 30,
            },
            str(uuid4()): {
                "pv_production_kWh": 10,

            },
            str(uuid4()): {
                "pv_production_kWh": 15,
            }
        }
        # Update the assets info for the first time
        self.assets_info.update({}, core_stats, "")
        expected_res = {
            "number_of_load_type": 3,
            "number_of_pv_type": 2,
            "total_energy_demand_kwh": 0.06,
            "total_energy_generated_kwh": 25
        }
        actual_res = {key: self.assets_info.raw_results[key] for key in expected_res.keys()}
        assert expected_res == actual_res

        # Update the assets info for the second time in order to see that total_energy_demand_kwh
        # is not but total_energy_generated_kwh is accumulated:
        self.assets_info.update({}, core_stats, "")
        expected_res = {
            "number_of_load_type": 3,
            "number_of_pv_type": 2,
            "total_energy_demand_kwh": 0.06,
            "total_energy_generated_kwh": 50
        }
        actual_res = {key: self.assets_info.raw_results[key] for key in expected_res.keys()}
        assert expected_res == actual_res

    def test_update_from_repr(self):
        area_representation = {
            "type": "Area",
            "children":
                [
                    {
                        "type": "FinitePowerPlant",
                        "max_available_power_kW": 15
                    },
                    {
                        "type": "FinitePowerPlant",
                        "max_available_power_kW": 30
                    },
                    {
                        "type": "Storage",
                        "battery_capacity_kWh": 25,
                    },
                    {
                        "type": "Storage",
                        "battery_capacity_kWh": 20
                    },
                    {
                        "type": "Area",
                        "children":
                            [
                                {
                                    "type": "Load"
                                },
                                {
                                    "type": "MarketMaker"
                                }
                            ]
                    },
                    {
                        "type": "Area",
                        "children":
                            [
                                {
                                    "type": "Load"
                                },
                                {
                                    "type": "MarketMaker"
                                },
                                {
                                    "type": "Load"
                                },
                                {
                                    "type": "MarketMaker"
                                }
                            ]
                    }
                ]
        }
        self.assets_info.update_from_repr(area_representation)
        expected_res = {
            "number_of_storage_type": 2,
            "total_energy_capacity_kwh": 45,
            "number_of_power_plant_type": 2,
            "max_power_plant_power_kw": 45,
            "number_of_house_type": 2,
            "avg_assets_per_house": 3
        }
        actual_res = {key: self.assets_info.raw_results[key] for key in expected_res.keys()}
        assert expected_res == actual_res
