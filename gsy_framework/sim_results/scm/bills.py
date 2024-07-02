from typing import Dict

from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import scenario_representation_traversal


class SCMBills(ResultsBaseClass):
    """Class to compute the energy bills of a home."""

    def __init__(self):
        self.bills_results = {}
        self.bills_redis_results = {}
        self._cumulative_fee_all_markets_whole_sim = 0.

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([
            self.bills_results, self.bills_redis_results])

    @staticmethod
    def _empty_bills_dict() -> Dict:
        return {
            "base_energy_bill": 0.,
            "gsy_energy_bill": 0.,
            "bought_from_community": 0.,
            "spent_to_community": 0.,
            "bought_from_grid": 0.,
            "spent_to_grid": 0.,
            "sold_to_grid": 0.,
            "sold_to_community": 0.,
            "earned_from_grid": 0.,
            "earned_from_community": 0.,
            "home_balance_kWh": 0.,
            "home_balance": 0.,
            "base_energy_bill_excl_revenue": 0.,
            "gsy_energy_bill_excl_revenue": 0.,
            "gsy_energy_bill_excl_revenue_without_fees": 0.,
            "gsy_energy_bill_revenue": 0.,
            "gsy_energy_bill_excl_fees": 0.,
            "gsy_total_benefit": 0.,
            "savings": 0.,
            "grid_fees": 0.,
            "grid_fees_percent": 0.,
            "export_grid_fees": 0.,
            "fees": {},
        }

    def update(self, area_result_dict, core_stats, current_market_slot):
        """SCM bills are not accumulative"""
        if not self._has_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return

        for area, _ in scenario_representation_traversal(area_result_dict):
            if not area.get("children"):
                continue

            if "bills" not in core_stats[area["uuid"]] or not core_stats[area["uuid"]]["bills"]:
                continue

            if area["uuid"] not in self.bills_redis_results:
                self.bills_redis_results[area["uuid"]] = self._empty_bills_dict()

            self.bills_redis_results[area["uuid"]] = core_stats[area["uuid"]]["bills"]
            self.bills_results[area["name"]] = core_stats[area["uuid"]]["bills"]

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        self.bills_redis_results[area_dict["uuid"]] = last_known_state_data
        self.bills_results[area_dict["name"]] = last_known_state_data

    def restore_cumulative_fees_whole_sim(self, cumulative_fees):
        """Replace the existing cumulative fees with the fees provided as argument."""
        self._cumulative_fee_all_markets_whole_sim = cumulative_fees

    # pylint: disable=arguments-differ
    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        raise NotImplementedError(
            "Bills endpoint supports only global results, merge not supported.")

    @property
    def raw_results(self):
        return self.bills_results

    @property
    def ui_formatted_results(self):
        return self.bills_redis_results
