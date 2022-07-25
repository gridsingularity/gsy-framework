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
from copy import copy
from typing import Dict, List
from dataclasses import dataclass
import logging

from gsy_framework.sim_results import (
    is_load_node_type, is_buffer_node_type, is_prosumer_node_type, is_producer_node_type)
from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import if_not_in_list_append


@dataclass
class SCMKPIState:
    """Accumulates results that are needed for the KPI calculation of one area."""
    total_energy_demanded_wh: float = 0.
    total_energy_produced_wh: float = 0.
    total_self_consumption_wh: float = 0.
    utility_bill: float = 0.
    gsy_e_cost: float = 0.
    fit_revenue: float = 0.

    def update(self, energy_demanded_wh: float, energy_produced_wh: float,
               self_consumption_wh: float, utility_bill: float, gsy_e_cost: float,
               fit_revenue: float):
        self.total_energy_demanded_wh += energy_demanded_wh
        self.total_energy_produced_wh += energy_produced_wh
        self.total_self_consumption_wh += self_consumption_wh
        self.utility_bill += utility_bill
        self.gsy_e_cost += gsy_e_cost
        self.fit_revenue += fit_revenue


class SCMKPI(ResultsBaseClass):
    """Handle calculation of KPI and savings KPI"""

    def __init__(self):
        self.performance_indices: Dict[str, Dict] = {}
        self.performance_indices_redis: Dict[str, Dict] = {}
        self._state: Dict[str, SCMKPIState] = {}

    def memory_allocation_size_kb(self):
        """Return memory allocation of object in kb"""
        return self._calculate_memory_allocated_by_objects([
            self.performance_indices, self.performance_indices_redis
        ])

    def __repr__(self):
        return f"KPI: {self.performance_indices}"

    def _calculate_area_performance_indices(self, area_dict: Dict, core_stats: Dict) -> Dict:
        """Entrypoint to be triggered after every market cycle to calculate
        respective area's KPIs"""

        after_meter_data = core_stats.get(area_dict["uuid"], {}).get("after_meter_data")
        bills = core_stats.get(area_dict["uuid"], {}).get("bills")
        if not after_meter_data or not bills:
            return {}

        if area_dict["uuid"] not in self._state:
            logging.warning(f"KPI state does not exist for this area, creating it.")
            self._state[area_dict["uuid"]] = SCMKPIState()
        state = self._state.get[area_dict["uuid"]]

        energy_demanded_wh = after_meter_data["consumption_kWh"] * 1000.0
        self_consumption_wh = after_meter_data["self_consumed_energy_kWh"] * 1000.0
        energy_produced_wh = after_meter_data["production_kWh"] * 1000.0
        utility_bill = after_meter_data["base_energy_bill"]
        gsy_e_cost = after_meter_data["gsy_energy_bill"]
        fit_revenue = after_meter_data["energy_surplus_kWh"] * after_meter_data["feed_in_tariff"]

        state.update(energy_demanded_wh, energy_produced_wh, self_consumption_wh,
                     utility_bill, gsy_e_cost, fit_revenue)

        # in case when the area doesn"t have any load demand
        if total_energy_demanded_wh <= 0:
            self_sufficiency = None
        elif total_self_consumption_wh >= total_energy_demanded_wh:
            self_sufficiency = 1.0
        else:
            self_sufficiency = total_self_consumption_wh / total_energy_demanded_wh

        if total_energy_produced_wh <= 0:
            self_consumption = None
        elif total_self_consumption_wh >= total_energy_produced_wh:
            self_consumption = 1.0
        else:
            self_consumption = total_self_consumption_wh / total_energy_produced_wh

        return {
            "name": area_dict["name"],
            "self_sufficiency": self_sufficiency,
            "self_consumption": self_consumption,
            "total_energy_demanded_wh": total_energy_demanded_wh,
            "total_energy_produced_wh": total_energy_produced_wh,
            "total_self_consumption_wh": total_self_consumption_wh,
            "utility_bill": utility_bill,
            "gsy_e_cost": gsy_e_cost,
            "fit_revenue": fit_revenue
        }

    def _get_ui_formatted_results(self, area_uuid: str) -> Dict:
        area_kpis = copy(self.performance_indices[area_uuid])
        if area_kpis["self_sufficiency"] is not None:
            area_kpis["self_sufficiency"] = area_kpis["self_sufficiency"] * 100
        else:
            area_kpis["self_sufficiency"] = 0.0
        if area_kpis["self_consumption"] is not None:
            area_kpis["self_consumption"] = area_kpis["self_consumption"] * 100
        else:
            area_kpis["self_consumption"] = 0.0

        # to be consistent with the old version, where no name is present in the kpi structure
        area_kpis.pop("name", None)

        return area_kpis

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str):
        """Entrypoint to iteratively updates all area's KPI"""
        # pylint: disable=arguments-renamed

        if (not self._has_update_parameters(area_dict, core_stats, current_market_slot) or
                not area_dict.get("children")):
            return

        self.area_uuid_cum_grid_fee_mapping[area_dict["uuid"]] = (
            self._accumulate_root_to_target_area_grid_fee(area_dict, core_stats))
        self.performance_indices[area_dict["uuid"]] = (
            self._calculate_area_performance_indices(area_dict, core_stats))

        for child in area_dict["children"]:
            if len(child["children"]) > 0:
                self.update(child, core_stats, current_market_slot)

        self._post_process_savings_kpis(area_dict)

        self.performance_indices_redis[area_dict["uuid"]] = (
            self._get_ui_formatted_results(area_dict["uuid"]))

    def _post_process_savings_kpis(self, area_dict: Dict) -> None:
        """
        Post process savings KPIs, that are also dependent on the savings KPIs of the children
            1. add utility_bill, fit_revenue, gsy_e_cost of child markets to the areas' values
            2. calculate base_case_cost, saving_absolute, saving_percentage for the area and
               add them to the self.performance_indices
        """
        if not area_dict.get("children") or area_dict["uuid"] not in self.savings_state:
            return

        for child in area_dict["children"]:
            if child["uuid"] in self.savings_state:
                self.performance_indices[area_dict["uuid"]]["utility_bill"] += (
                    self.savings_state[child["uuid"]].utility_bill)
                self.performance_indices[area_dict["uuid"]]["fit_revenue"] += (
                    self.savings_state[child["uuid"]].fit_revenue)
                self.performance_indices[area_dict["uuid"]]["gsy_e_cost"] += (
                    self.savings_state[child["uuid"]].gsy_e_cost)

        base_case_cost = (self.performance_indices[area_dict["uuid"]]["utility_bill"] -
                          self.performance_indices[area_dict["uuid"]]["fit_revenue"])
        saving_absolute = (base_case_cost -
                           self.performance_indices[area_dict["uuid"]]["gsy_e_cost"])
        saving_percentage = (abs((saving_absolute / base_case_cost) * 100)
                             if base_case_cost else None)

        self.performance_indices[area_dict["uuid"]]["base_case_cost"] = base_case_cost
        self.performance_indices[area_dict["uuid"]]["saving_absolute"] = saving_absolute
        self.performance_indices[area_dict["uuid"]]["saving_percentage"] = saving_percentage

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """Restore KPI for last known state"""
        if not last_known_state_data:
            return
        if area_dict["uuid"] not in self._state:
            self._state[area_dict["uuid"]] = SCMKPIState(
                total_energy_demanded_wh=last_known_state_data["total_energy_demanded_wh"],
                total_energy_produced_wh=last_known_state_data["total_energy_produced_wh"],
                total_self_consumption_wh=last_known_state_data["total_self_consumption_wh"],
                utility_bill=last_known_state_data.get("utility_bill", 0) or 0,
                fit_revenue=last_known_state_data.get("fit_revenue", 0) or 0,
                gsy_e_cost=(
                    last_known_state_data.get("gsy_e_cost", 0)
                    or last_known_state_data.get("d3a_cost", 0) or 0)
            )

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        # pylint: disable=arguments-differ
        raise NotImplementedError(
            "KPI endpoint supports only global results, merge not supported.")

    @property
    def raw_results(self):
        return self.performance_indices

    @property
    def ui_formatted_results(self):
        return self.performance_indices_redis
