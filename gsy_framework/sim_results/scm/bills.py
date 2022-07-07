from typing import Dict

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE
from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import scenario_representation_traversal


class SCMBills(ResultsBaseClass):
    """Class to compute the energy bills of a home."""

    def __init__(self):
        self.bills_results = {
            "aggregated": {},
            "current": {}
        }
        self.bills_redis_results = {
            "aggregated": {},
            "current": {}
        }
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
            "earned_from_grid": 0.,
            "home_balance_kWh": 0.,
            "home_balance": 0.,
            "gsy_energy_bill_excl_revenue": 0.,
            "gsy_energy_bill_excl_revenue_without_fees": 0.,
            "tax_surcharges": 0.,
            "grid_fees": 0.,
            "fixed_fee": 0.,
            "marketplace_fee": 0.,
            "energy_cost_percent": 0.,
            "grid_fees_percent": 0.,
            "tax_surcharges_percent": 0.,
            "marketplace_fees_percent": 0.,
            "fixed_fees_percent": 0.
        }

    def update(self, area_result_dict, core_stats, current_market_slot):
        if not self._has_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return

        for area, _ in scenario_representation_traversal(area_result_dict):
            if not area.get("children"):
                continue

            if "bills" not in core_stats[area["uuid"]]:
                continue

            if area["uuid"] not in self.bills_redis_results["aggregated"]:
                self.bills_redis_results["aggregated"][area["uuid"]] = self._empty_bills_dict()

            area_bills = {
                k: v + core_stats[area["uuid"]]["bills"].get(k, 0.)
                for k, v in self.bills_redis_results["aggregated"][area["uuid"]].items()
            }
            area_bills["savings"] = area_bills["base_energy_bill"] - area_bills["gsy_energy_bill"]
            area_bills["savings_percent"] = (
                (area_bills["savings"] / area_bills["base_energy_bill"]) * 100.0
                if area_bills["base_energy_bill"] > 0. else 0.
            )

            gsy_energy_bill_excl_revenue = (
                area_bills["gsy_energy_bill_excl_revenue"])
            if gsy_energy_bill_excl_revenue > FLOATING_POINT_TOLERANCE:
                area_bills["energy_cost_percent"] = (
                    (area_bills["gsy_energy_bill_excl_revenue_without_fees"] /
                     gsy_energy_bill_excl_revenue) * 100.
                )

                area_bills["grid_fees_percent"] = (
                    (area_bills["grid_fees"] / gsy_energy_bill_excl_revenue) * 100.
                )

                area_bills["tax_surcharges_percent"] = (
                    (area_bills["tax_surcharges"] / gsy_energy_bill_excl_revenue) * 100.
                )

                area_bills["fixed_fees_percent"] = (
                        (area_bills["fixed_fee"] / gsy_energy_bill_excl_revenue) * 100.
                )

                area_bills["marketplace_fees_percent"] = (
                        (area_bills["marketplace_fee"] / gsy_energy_bill_excl_revenue) * 100.
                )

            self.bills_redis_results["aggregated"][area["uuid"]] = area_bills
            self.bills_results["aggregated"][area["name"]] = area_bills

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