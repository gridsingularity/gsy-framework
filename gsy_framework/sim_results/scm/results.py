from typing import Dict

from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import scenario_representation_traversal


class SCMResults(ResultsBaseClass):
    """Class to compute the energy bills of a home."""

    def __init__(self):
        self.results = {}

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([self.results])

    def update(self, area_result_dict, core_stats, current_market_slot):
        """SCM results are not accumulative"""
        if not self._has_update_parameters(area_result_dict, core_stats, current_market_slot):
            return

        for area, _ in scenario_representation_traversal(area_result_dict):
            if not area.get("children"):
                continue

            if "bills" in core_stats[area["uuid"]] and core_stats[area["uuid"]]["bills"]:
                self.results[area["uuid"]] = core_stats[area["uuid"]]["bills"]

            after_meter_data = core_stats.get(area["uuid"], {}).get("after_meter_data")
            if after_meter_data:
                self.results[area["uuid"]].update(after_meter_data)

    # pylint: disable=arguments-differ
    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        raise NotImplementedError(
            "SCM results endpoint supports only global results, merge not supported."
        )

    @property
    def raw_results(self):
        return self.results

    @property
    def ui_formatted_results(self):
        return self.results

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        raise NotImplementedError("SCM results endpoint support state.")
