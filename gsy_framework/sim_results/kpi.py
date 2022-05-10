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

from gsy_framework.sim_results import (
    is_load_node_type, is_buffer_node_type, is_prosumer_node_type, is_producer_node_type)
from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import if_not_in_list_append


class KPIState:
    """Calculate Key Performance Indicator of Area"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        self.producer_list: List = []
        self.consumer_list: List = []
        self.areas_to_trace_list: List = []
        self.ess_list: List = []
        self.buffer_list: List = []
        self.total_energy_demanded_wh: float = 0.
        self.demanded_buffer_wh: float = 0.
        self.total_energy_produced_wh: float = 0.
        self.total_self_consumption_wh: float = 0.
        self.self_consumption_buffer_wh: float = 0.

    def accumulate_devices(self, area_dict: Dict):
        """Accumulate all child devices with respective types"""
        for child in area_dict["children"]:
            if is_producer_node_type(child):
                if_not_in_list_append(self.producer_list, child["uuid"])
                if_not_in_list_append(self.areas_to_trace_list, child["parent_uuid"])
            elif is_load_node_type(child):
                if_not_in_list_append(self.consumer_list, child["uuid"])
                if_not_in_list_append(self.areas_to_trace_list, child["parent_uuid"])
            elif is_prosumer_node_type(child):
                if_not_in_list_append(self.ess_list, child["uuid"])
            elif is_buffer_node_type(child):
                if_not_in_list_append(self.buffer_list, child["uuid"])
            if child["children"]:
                self.accumulate_devices(child)

    def _accumulate_total_energy_demanded(self, area_dict: Dict, core_stats: Dict):
        for child in area_dict["children"]:
            child_stats = core_stats.get(child["uuid"], {})
            if is_load_node_type(child):
                self.total_energy_demanded_wh += child_stats.get("total_energy_demanded_wh", 0)
            if child["children"]:
                self._accumulate_total_energy_demanded(child, core_stats)

    def _accumulate_self_production(self, trade: Dict):
        # Trade seller_id origin should be equal to the trade seller_id in order to
        # not double count trades in higher hierarchies
        if (trade["seller_origin_id"] in self.producer_list and
                trade["seller_origin_id"] == trade["seller_id"]):
            self.total_energy_produced_wh += trade["energy"] * 1000

    def _accumulate_self_consumption(self, trade: Dict):
        # Trade buyer_id origin should be equal to the trade buyer_id in order to
        # not double count trades in higher hierarchies
        if (trade["seller_origin_id"] in self.producer_list and
                trade["buyer_origin_id"] in self.consumer_list and
                trade["buyer_origin_id"] == trade["buyer_id"]):
            self.total_self_consumption_wh += trade["energy"] * 1000

    def _accumulate_self_consumption_buffer(self, trade: Dict):
        if (trade["seller_origin_id"] in self.producer_list and
                trade["buyer_origin_id"] in self.ess_list):
            self.self_consumption_buffer_wh += trade["energy"] * 1000

    def _dissipate_self_consumption_buffer(self, trade: Dict):
        if trade["seller_origin_id"] in self.ess_list:
            # self_consumption_buffer needs to be exhausted to total_self_consumption
            # if sold to internal consumer
            if (trade["buyer_origin_id"] in self.consumer_list and
                    trade["buyer_origin_id"] == trade["buyer_id"] and
                    self.self_consumption_buffer_wh > 0):
                if (self.self_consumption_buffer_wh - trade["energy"] * 1000) > 0:
                    self.self_consumption_buffer_wh -= trade["energy"] * 1000
                    self.total_self_consumption_wh += trade["energy"] * 1000
                else:
                    self.total_self_consumption_wh += self.self_consumption_buffer_wh
                    self.self_consumption_buffer_wh = 0
            # self_consumption_buffer needs to be exhausted if sold to any external agent
            elif (trade["buyer_origin_id"] not in [*self.ess_list, *self.consumer_list] and
                    trade["buyer_origin_id"] == trade["buyer_id"] and
                    self.self_consumption_buffer_wh > 0):
                if (self.self_consumption_buffer_wh - trade["energy"] * 1000) > 0:
                    self.self_consumption_buffer_wh -= trade["energy"] * 1000
                else:
                    self.self_consumption_buffer_wh = 0

    def _accumulate_infinite_consumption(self, trade: Dict):
        """
        If the InfiniteBus is a seller_id of the trade when below the referenced area and bought
        by any of child devices.
        * total_self_consumption_wh needs to accumulated.
        * total_energy_produced_wh also needs to accumulated accounting of what
        the InfiniteBus has produced.
        """
        if (trade["seller_origin_id"] in self.buffer_list and
                trade["buyer_origin_id"] in self.consumer_list and
                trade["buyer_origin_id"] == trade["buyer_id"]):
            self.total_self_consumption_wh += trade["energy"] * 1000
            self.total_energy_produced_wh += trade["energy"] * 1000

    def _dissipate_infinite_consumption(self, trade: Dict):
        """
        If the InfiniteBus is a buyer_id of the trade when below the referenced area
        and sold by any of child devices.
        total_self_consumption_wh needs to accumulated.
        demanded_buffer_wh also needs to accumulated accounting of what
        the InfiniteBus has consumed/demanded.
        """
        if (trade["buyer_origin_id"] in self.buffer_list and
                trade["seller_origin_id"] in self.producer_list
                and trade["seller_origin_id"] == trade["seller_id"]):
            self.total_self_consumption_wh += trade["energy"] * 1000
            self.demanded_buffer_wh += trade["energy"] * 1000

    def _accumulate_energy_trace(self, core_stats):
        for target_area_uuid in self.areas_to_trace_list:
            target_core_stats = core_stats.get(target_area_uuid, {})
            for trade in target_core_stats.get("trades", []):
                self._accumulate_self_consumption(trade)
                self._accumulate_self_production(trade)
                self._accumulate_self_consumption_buffer(trade)
                self._dissipate_self_consumption_buffer(trade)
                self._accumulate_infinite_consumption(trade)
                self._dissipate_infinite_consumption(trade)

    def update_area_kpi(self, area_dict: Dict, core_stats: Dict):
        """Update kpi after every market cycle"""
        self.total_energy_demanded_wh = 0
        self._accumulate_total_energy_demanded(area_dict, core_stats)
        self._accumulate_energy_trace(core_stats)


class SavingsKPI:
    """Responsible for generating comparative savings from feed-in tariff vs GSY-E"""

    def __init__(self):
        self.producer_ess_set = set()  # keeps set of house's producing/ess devices
        self.consumer_ess_set = set()  # keeps set of house's consuming/ess devices
        self.fit_revenue = 0.  # revenue achieved by producing selling energy via FIT scheme
        self.utility_bill = 0.  # cost of energy purchase from energy supplier
        self.gsy_e_cost = 0.  # standard cost of a house participating in GSy Exchange

    def calculate_savings_kpi(self, area_dict: Dict, core_stats: Dict, grid_fee_along_path: float):
        """Calculates the referenced saving from feed-in tariff based participation vs GSY-E
        Args:
            area_dict: contain nested area info
            core_stats: contain area's raw/key statistics
            grid_fee_along_path: grid_fee_along_the_path -
            cumulative grid fee from root to target area

        """
        self._populate_consumer_producer_sets(area_dict)

        feed_in_tariff = self._get_feed_in_tariff_rate_excluding_path_grid_fees(
            core_stats.get(area_dict["uuid"], {}), grid_fee_along_path)
        market_maker_rate = self._get_market_maker_rate_including_path_grid_fees(
            core_stats.get(area_dict["uuid"], {}), grid_fee_along_path)

        for trade in core_stats.get(area_dict["uuid"], {}).get("trades", []):
            if trade["seller_origin_id"] in self.producer_ess_set:
                if feed_in_tariff > 0:
                    self.fit_revenue += feed_in_tariff * trade["energy"]
                self.gsy_e_cost -= trade["price"] - trade["fee_price"]
            if trade["buyer_origin_id"] in self.consumer_ess_set:
                self.utility_bill += market_maker_rate * trade["energy"]
                self.gsy_e_cost += trade["price"]

    def _populate_consumer_producer_sets(self, area_dict: Dict):
        """
        Populate sets of device classes.
        Args:
            area_dict: It contains the respective area's core info
        """
        for child in area_dict["children"]:
            if is_producer_node_type(child):
                self.producer_ess_set.add(child["uuid"])
            elif is_load_node_type(child):
                self.consumer_ess_set.add(child["uuid"])
            elif is_prosumer_node_type(child):
                self.producer_ess_set.add(child["uuid"])
                self.consumer_ess_set.add(child["uuid"])

    @staticmethod
    def _get_feed_in_tariff_rate_excluding_path_grid_fees(
            area_core_stat: Dict, path_grid_fee: float):
        """
        Args:
            area_core_stat: It contains the respective area's core statistics
            path_grid_fee: Cumulative fee from root to target area
        Returns: feed-in tariff excluding accumulated grid fee from root to target area
        """
        return area_core_stat.get("feed_in_tariff", 0.) - path_grid_fee

    @staticmethod
    def _get_market_maker_rate_including_path_grid_fees(
            area_core_stat: Dict, path_grid_fee: float):
        """
        Args:
            area_core_stat: It contains the respective area's core statistics
            path_grid_fee: Cumulative fee from root to target area
        Returns: market_maker_rate including accumulated grid fee from root to target area
        """
        return area_core_stat.get("market_maker_rate", 0.) + path_grid_fee

    def to_dict(self):
        """
        Returns: key calculated parameters in dict type
        """
        return {"utility_bill": self.utility_bill,
                "fit_revenue": self.fit_revenue,
                "gsy_e_cost": self.gsy_e_cost}


class KPI(ResultsBaseClass):
    """Handle calculation of KPI and savings KPI"""

    def __init__(self):
        self.performance_indices: Dict[str, Dict] = {}
        self.performance_indices_redis: Dict[str, Dict] = {}
        self.state: Dict[str, KPIState] = {}
        self.savings_state: Dict[str, SavingsKPI] = {}

        # mapping of area_uuid and the corresponding cumulative grid-free along the path
        # from root-area to the target-area
        self.area_uuid_cum_grid_fee_mapping: Dict = {}

    def memory_allocation_size_kb(self):
        """Return memory allocation of object in kb"""
        return self._calculate_memory_allocated_by_objects([
            self.performance_indices, self.performance_indices_redis
        ])

    def __repr__(self):
        return f"KPI: {self.performance_indices}"

    def _init_states(self, area_dict: Dict):
        if area_dict["uuid"] not in self.state:
            self.state[area_dict["uuid"]] = KPIState()
        if area_dict["uuid"] not in self.savings_state and area_dict.get("parent_uuid"):
            # savings KPI for the root area is not interesting,
            # because the market maker usually resides there. Therefor the calculation is skipped
            self.savings_state[area_dict["uuid"]] = SavingsKPI()

    def _calculate_area_performance_indices(self, area_dict: Dict, core_stats: Dict) -> Dict:
        """Entrypoint to be triggered after every market cycle to calculate
        respective area's KPIs"""

        self._init_states(area_dict)

        self.state[area_dict["uuid"]].accumulate_devices(area_dict)

        self.state[area_dict["uuid"]].update_area_kpi(area_dict, core_stats)
        total_energy_demanded_wh = (
                self.state[area_dict["uuid"]].total_energy_demanded_wh +
                self.state[area_dict["uuid"]].demanded_buffer_wh)

        # in case when the area doesn"t have any load demand
        if total_energy_demanded_wh <= 0:
            self_sufficiency = None
        elif self.state[area_dict["uuid"]].total_self_consumption_wh >= total_energy_demanded_wh:
            self_sufficiency = 1.0
        else:
            self_sufficiency = (self.state[area_dict["uuid"]].total_self_consumption_wh /
                                total_energy_demanded_wh)

        if self.state[area_dict["uuid"]].total_energy_produced_wh <= 0:
            self_consumption = None
        elif (self.state[area_dict["uuid"]].total_self_consumption_wh >=
              self.state[area_dict["uuid"]].total_energy_produced_wh):
            self_consumption = 1.0
        else:
            self_consumption = (self.state[area_dict["uuid"]].total_self_consumption_wh /
                                self.state[area_dict["uuid"]].total_energy_produced_wh)

        kpi_parm_dict = {
            "name": area_dict["name"],
            "self_sufficiency": self_sufficiency,
            "self_consumption": self_consumption,
            "total_energy_demanded_wh": total_energy_demanded_wh,
            "demanded_buffer_wh": self.state[area_dict["uuid"]].demanded_buffer_wh,
            "self_consumption_buffer_wh": self.state[area_dict["uuid"]].self_consumption_buffer_wh,
            "total_energy_produced_wh": self.state[area_dict["uuid"]].total_energy_produced_wh,
            "total_self_consumption_wh": self.state[area_dict["uuid"]].total_self_consumption_wh,
        }

        if area_dict["uuid"] in self.savings_state:
            self.savings_state[area_dict["uuid"]].calculate_savings_kpi(
                area_dict, core_stats, self.area_uuid_cum_grid_fee_mapping[area_dict["uuid"]])
            kpi_parm_dict.update(self.savings_state[area_dict["uuid"]].to_dict())

        return kpi_parm_dict

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

    def _accumulate_root_to_target_area_grid_fee(self, area_dict, core_stats):
        parent_fee = self.area_uuid_cum_grid_fee_mapping.get(
            area_dict.get("parent_uuid", None), 0.)
        area_fee = core_stats.get(area_dict.get("uuid", None), {}).get("const_fee_rate", 0.)
        return parent_fee + area_fee

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """Restore KPI for last known state"""
        if not last_known_state_data:
            return
        if area_dict["uuid"] not in self.state:
            self.state[area_dict["uuid"]] = KPIState()
            self.state[area_dict["uuid"]].demanded_buffer_wh = (
                last_known_state_data["demanded_buffer_wh"])
            self.state[area_dict["uuid"]].total_energy_demanded_wh = (
                last_known_state_data["total_energy_demanded_wh"])
            self.state[area_dict["uuid"]].total_energy_produced_wh = (
                last_known_state_data["total_energy_produced_wh"])
            self.state[area_dict["uuid"]].total_self_consumption_wh = (
                last_known_state_data["total_self_consumption_wh"])
            self.state[area_dict["uuid"]].self_consumption_buffer_wh = (
                last_known_state_data["self_consumption_buffer_wh"])
        if area_dict["uuid"] not in self.savings_state:
            self.savings_state[area_dict["uuid"]] = SavingsKPI()
            self.savings_state[area_dict["uuid"]].utility_bill = (
                last_known_state_data.get("utility_bill", 0)) or 0
            self.savings_state[area_dict["uuid"]].fit_revenue = (
                last_known_state_data.get("fit_revenue", 0)) or 0
            self.savings_state[area_dict["uuid"]].gsy_e_cost = (
                last_known_state_data.get("gsy_e_cost", 0)
                or last_known_state_data.get("d3a_cost", 0)) or 0

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
