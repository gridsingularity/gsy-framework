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
import logging
from copy import copy
from dataclasses import dataclass, asdict
from typing import Dict

from gsy_framework.sim_results.results_abc import ResultsBaseClass


@dataclass
class SCMKPIState:
    # pylint: disable=too-many-instance-attributes
    """Accumulates results that are needed for the KPI calculation of one area."""
    total_energy_demanded_wh: float = 0.
    total_energy_produced_wh: float = 0.
    total_self_consumption_wh: float = 0.
    total_base_energy_cost: float = 0.
    total_gsy_e_cost: float = 0.
    total_base_energy_cost_excl_revenue: float = 0.
    total_gsy_e_cost_excl_revenue: float = 0.
    total_fit_revenue: float = 0.
    energy_demanded_wh: float = 0.
    energy_produced_wh: float = 0.
    self_consumption_wh: float = 0.
    base_energy_cost: float = 0.
    gsy_e_cost: float = 0.
    base_energy_cost_excl_revenue: float = 0.
    gsy_e_cost_excl_revenue: float = 0.
    fit_revenue: float = 0.

    def to_dict(self):
        """Dict representation of the KPI state class."""
        output_dict = asdict(self)
        output_dict.update({
            "self_sufficiency": self.self_sufficiency,
            "self_consumption": self.self_consumption,
            "saving_absolute": self.saving_absolute,
            "saving_precentage": self.saving_percentage
        })
        return output_dict

    def update(self, energy_demanded_wh: float, energy_produced_wh: float,
               self_consumption_wh: float, base_energy_cost: float,
               base_energy_cost_excl_revenue: float, gsy_e_cost: float,
               gsy_e_cost_excl_revenue: float, fit_revenue: float):
        # pylint: disable=too-many-arguments
        """Update both the aggregated state members and the raw state members."""
        self.energy_demanded_wh = energy_demanded_wh
        self.energy_produced_wh = energy_produced_wh
        self.self_consumption_wh = self_consumption_wh
        self.base_energy_cost = base_energy_cost
        self.gsy_e_cost = gsy_e_cost
        self.base_energy_cost_excl_revenue = base_energy_cost_excl_revenue
        self.gsy_e_cost_excl_revenue = gsy_e_cost_excl_revenue
        self.fit_revenue = fit_revenue
        self.total_energy_demanded_wh += energy_demanded_wh
        self.total_energy_produced_wh += energy_produced_wh
        self.total_self_consumption_wh += self_consumption_wh
        self.total_base_energy_cost += base_energy_cost
        self.total_gsy_e_cost += gsy_e_cost
        self.total_base_energy_cost_excl_revenue += base_energy_cost_excl_revenue
        self.total_gsy_e_cost_excl_revenue += gsy_e_cost_excl_revenue
        self.total_fit_revenue += fit_revenue

    @property
    def saving_absolute(self):
        """Return absolute bill savings value for the area."""
        return self.total_base_energy_cost_excl_revenue - self.total_gsy_e_cost_excl_revenue

    @property
    def saving_percentage(self):
        """Return percentage bill savings for the area."""
        return (abs((self.saving_absolute / self.total_base_energy_cost_excl_revenue) * 100)
                if self.total_base_energy_cost_excl_revenue else None)

    @property
    def self_sufficiency(self):
        """Calculate area self sufficiency. Value range 0.0-1.0."""
        if self.total_energy_demanded_wh <= 0:
            return None

        if self.total_self_consumption_wh >= self.total_energy_demanded_wh:
            return 1.0

        return self.total_self_consumption_wh / self.total_energy_demanded_wh

    @property
    def self_consumption(self):
        """Calculate area self consumption. Value range 0.0-1.0."""
        if self.total_energy_produced_wh <= 0:
            return None
        if self.total_self_consumption_wh >= self.total_energy_produced_wh:
            return 1.0

        return self.total_self_consumption_wh / self.total_energy_produced_wh


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
            logging.warning("KPI state does not exist for this area, creating it.")
            self._state[area_dict["uuid"]] = SCMKPIState()
        state = self._state[area_dict["uuid"]]

        energy_demanded_wh = after_meter_data["consumption_kWh"] * 1000.0
        self_consumption_wh = after_meter_data["self_consumed_energy_kWh"] * 1000.0
        energy_produced_wh = after_meter_data["production_kWh"] * 1000.0
        base_energy_cost = bills["base_energy_bill"]
        base_energy_cost_excl_revenue = bills["base_energy_bill_excl_revenue"]
        gsy_e_cost = bills["gsy_energy_bill"]
        gsy_e_cost_excl_revenue = bills["gsy_energy_bill_excl_revenue"]
        fit_revenue = bills["sold_to_community"] + bills["sold_to_grid"]

        state.update(energy_demanded_wh, energy_produced_wh, self_consumption_wh,
                     base_energy_cost, base_energy_cost_excl_revenue, gsy_e_cost,
                     gsy_e_cost_excl_revenue, fit_revenue)

        return {
            "name": area_dict["name"],
            **state.to_dict()
        }

    def _get_ui_formatted_results(self, area_uuid: str) -> Dict:
        area_kpis = copy(self.performance_indices[area_uuid])
        if area_kpis.get("self_sufficiency") is not None:
            area_kpis["self_sufficiency"] = area_kpis["self_sufficiency"] * 100
        else:
            area_kpis["self_sufficiency"] = 0.0
        if area_kpis.get("self_consumption") is not None:
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

        self.performance_indices[area_dict["uuid"]] = (
            self._calculate_area_performance_indices(area_dict, core_stats))

        for child in area_dict["children"]:
            if "children" in child and len(child["children"]) > 0:
                self.update(child, core_stats, current_market_slot)

        self.performance_indices_redis[area_dict["uuid"]] = (
            self._get_ui_formatted_results(area_dict["uuid"]))

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """Restore KPI for last known state"""
        if not last_known_state_data:
            return
        if area_dict["uuid"] not in self._state:
            self._state[area_dict["uuid"]] = SCMKPIState(
                total_energy_demanded_wh=last_known_state_data["total_energy_demanded_wh"],
                total_energy_produced_wh=last_known_state_data["total_energy_produced_wh"],
                total_self_consumption_wh=last_known_state_data["total_self_consumption_wh"],
                total_base_energy_cost=last_known_state_data.get("total_base_energy_cost", 0) or 0,
                total_fit_revenue=last_known_state_data.get("total_fit_revenue", 0) or 0,
                total_gsy_e_cost=last_known_state_data.get("total_gsy_e_cost", 0) or 0,
                total_base_energy_cost_excl_revenue=last_known_state_data.get(
                    "total_base_energy_cost_excl_revenue", 0) or 0,
                total_gsy_e_cost_excl_revenue=last_known_state_data.get(
                    "total_gsy_e_cost_excl_revenue", 0) or 0,
                energy_demanded_wh=last_known_state_data["energy_demanded_wh"],
                energy_produced_wh=last_known_state_data["energy_produced_wh"],
                self_consumption_wh=last_known_state_data["self_consumption_wh"],
                base_energy_cost=last_known_state_data.get("base_energy_cost", 0) or 0,
                base_energy_cost_excl_revenue=last_known_state_data.get(
                    "base_energy_cost_excl_revenue", 0) or 0,
                fit_revenue=last_known_state_data.get("fit_revenue", 0) or 0,
                gsy_e_cost=last_known_state_data.get("gsy_e_cost", 0) or 0,
                gsy_e_cost_excl_revenue=last_known_state_data.get(
                    "gsy_e_cost_excl_revenue", 0) or 0
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
