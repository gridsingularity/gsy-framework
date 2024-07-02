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
from typing import Dict

from gsy_framework.sim_results.results_abc import ResultsBaseClass


class SCMKPI(ResultsBaseClass):
    """Handle calculation of KPI and savings KPI"""

    def __init__(self):
        self.performance_indices: Dict[str, Dict] = {}
        self.performance_indices_redis: Dict[str, Dict] = {}

    def memory_allocation_size_kb(self):
        """Return memory allocation of object in kb"""
        return self._calculate_memory_allocated_by_objects([
            self.performance_indices, self.performance_indices_redis
        ])

    def __repr__(self):
        return f"KPI: {self.performance_indices}"

    @staticmethod
    def _calculate_area_performance_indices(area_dict: Dict, core_stats: Dict) -> Dict:
        """Entrypoint to be triggered after every market cycle to calculate
        respective area's KPIs"""

        after_meter_data = core_stats.get(area_dict["uuid"], {}).get("after_meter_data")
        bills = core_stats.get(area_dict["uuid"], {}).get("bills")
        if not after_meter_data or not bills:
            return {}

        return {
            "name": area_dict["name"],
            "energy_demanded_kWh": after_meter_data["consumption_kWh"],
            "self_consumption_kWh": after_meter_data["self_consumed_energy_kWh"],
            "energy_produced_kWh": after_meter_data["production_kWh"],
            "asset_energy_requirements_kWh": after_meter_data.get(
                "asset_energy_requirements_kWh", {}),
        }

    def _get_ui_formatted_results(self, area_uuid: str) -> Dict:
        area_kpis = copy(self.performance_indices[area_uuid])
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
