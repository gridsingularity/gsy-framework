from typing import Dict, List

from d3a_interface.sim_results.results_abc import ResultsBaseClass


class SimulationAssetsInfo(ResultsBaseClass):
    FIELDS = ['number_of_house_type', 'avg_assets_per_house', 'number_of_load_type',
              'total_energy_demand_kwh', 'number_of_pv_type', 'total_energy_generated_kwh',
              'number_of_storage_type', 'total_energy_capacity_kwh', 'number_of_power_plant_type',
              'max_power_plant_power_kw']

    def __init__(self):
        for field in SimulationAssetsInfo.FIELDS:
            setattr(self, field, 0)

    @staticmethod
    def merge_results_to_global(market_results: Dict, global_results: Dict, slot_list: List):
        pass

    def update(self, area_result_dict, core_stats, current_market_slot):
        updated_results_dict = {field: 0 for field in SimulationAssetsInfo.FIELDS}
        for area_uuid, area_result in core_stats.items():
            if 'total_energy_demanded_wh' in area_result:
                updated_results_dict['number_of_load_type'] += 1
                updated_results_dict['total_energy_demand_kwh'] += area_result['total_energy_demanded_wh']/ 1000.0
            elif 'pv_production_kWh' in area_result:
                updated_results_dict['number_of_pv_type'] += 1
                updated_results_dict['total_energy_generated_kwh'] += area_result['pv_production_kWh']
            elif 'Storage' in area_result:  # Needs to update the result sent from d3a to send the capacity
                pass
            elif 'FinitePowerPlant' in area_result:  # Needs to update the result sent from d3a to send the power
                pass

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        pass

    @property
    def raw_results(self):
        return {key: getattr(self, key) for key in SimulationAssetsInfo.FIELDS}

    def memory_allocation_size_kb(self):
        return 0

