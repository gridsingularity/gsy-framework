from typing import Dict, List

from d3a_interface.sim_results import is_finite_power_plant_node_type, is_prosumer_node_type
from d3a_interface.sim_results.results_abc import ResultsBaseClass
from d3a_interface.utils import scenario_representation_traversal, HomeRepresentationUtils


class SimulationAssetsInfo(ResultsBaseClass):
    FIELDS = ["number_of_house_type", "avg_assets_per_house", "number_of_load_type",
              "total_energy_demand_kwh", "number_of_pv_type", "total_energy_generated_kwh",
              "number_of_storage_type", "total_energy_capacity_kwh", "number_of_power_plant_type",
              "max_power_plant_power_kw"]

    def __init__(self):
        self.assets_info = {field: 0 for field in SimulationAssetsInfo.FIELDS}

    @staticmethod
    def merge_results_to_global(market_results: Dict, global_results: Dict, slot_list: List):
        raise NotImplementedError(
            "Assets Info endpoint supports only global results, "
            "merge not supported.")

    def update(self, area_result_dict: Dict, core_stats: Dict, current_market_slot: str):
        # total_energy_demanded_wh is already accumulated value and should only be replaced
        updated_results_dict = {
            "number_of_load_type": 0,
            "total_energy_demand_kwh": 0,
            "number_of_pv_type": 0,
            "total_energy_generated_kwh": self.assets_info["total_energy_generated_kwh"]
        }
        for area_result in core_stats.values():
            if "total_energy_demanded_wh" in area_result:
                updated_results_dict["number_of_load_type"] += 1
                updated_results_dict["total_energy_demand_kwh"] += \
                    area_result["total_energy_demanded_wh"] / 1000.0
            elif "pv_production_kWh" in area_result:
                updated_results_dict["number_of_pv_type"] += 1
                updated_results_dict["total_energy_generated_kwh"] += \
                    area_result["pv_production_kWh"]

            self.assets_info.update(updated_results_dict)

    def update_from_repr(self, area_representation: Dict):
        updated_results_dict = {
            "number_of_storage_type": 0,
            "total_energy_capacity_kwh": 0,
            "number_of_power_plant_type": 0,
            "max_power_plant_power_kw": 0,
            "number_of_house_type": 0,
            "avg_assets_per_house": 0
        }
        for area_dict, _ in scenario_representation_traversal(area_representation):
            if is_prosumer_node_type(area_dict):
                updated_results_dict["number_of_storage_type"] += 1
                updated_results_dict["total_energy_capacity_kwh"] +=\
                    area_dict.get("battery_capacity_kWh", 0)
            elif is_finite_power_plant_node_type(area_dict):
                updated_results_dict["number_of_power_plant_type"] += 1
                updated_results_dict["max_power_plant_power_kw"] +=\
                    area_dict.get("max_available_power_kW", 0)

        updated_results_dict["number_of_house_type"],\
            updated_results_dict["avg_assets_per_house"] = \
            HomeRepresentationUtils.calculate_home_area_stats_from_repr_dict(area_representation)

        self.assets_info.update(updated_results_dict)

    def restore_assets_info(self, assets_info):
        """Used for restoring the state of the assets_info."""
        if assets_info:
            self.assets_info = assets_info

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        pass

    @property
    def raw_results(self):
        return self.assets_info

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([self.assets_info, ])
