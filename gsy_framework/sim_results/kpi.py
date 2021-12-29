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
from typing import Dict
from gsy_framework.utils import if_not_in_list_append
from gsy_framework.sim_results import (
    is_load_node_type, is_buffer_node_type, is_prosumer_node_type, is_producer_node_type,
    has_grand_children)
from gsy_framework.sim_results.results_abc import ResultsBaseClass


class KPIState:
    """Calculate Key Performance Indicator of Area"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.producer_list: list = []
        self.consumer_list: list = []
        self.areas_to_trace_list: list = []
        self.ess_list: list = []
        self.buffer_list: list = []
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
        if trade["seller_origin_id"] in self.producer_list and \
                trade["seller_origin_id"] == trade["seller_id"]:
            self.total_energy_produced_wh += trade["energy"] * 1000

    def _accumulate_self_consumption(self, trade: Dict):
        # Trade buyer_id origin should be equal to the trade buyer_id in order to
        # not double count trades in higher hierarchies
        if trade["seller_origin_id"] in self.producer_list and \
                trade["buyer_origin_id"] in self.consumer_list and \
                trade["buyer_origin_id"] == trade["buyer_id"]:
            self.total_self_consumption_wh += trade["energy"] * 1000

    def _accumulate_self_consumption_buffer(self, trade: Dict):
        if trade["seller_origin_id"] in self.producer_list and \
                trade["buyer_origin_id"] in self.ess_list:
            self.self_consumption_buffer_wh += trade["energy"] * 1000

    def _dissipate_self_consumption_buffer(self, trade: Dict):
        if trade["seller_origin_id"] in self.ess_list:
            # self_consumption_buffer needs to be exhausted to total_self_consumption
            # if sold to internal consumer
            if trade["buyer_origin_id"] in self.consumer_list and \
                    trade["buyer_origin_id"] == trade["buyer_id"] and \
                    self.self_consumption_buffer_wh > 0:
                if (self.self_consumption_buffer_wh - trade["energy"] * 1000) > 0:
                    self.self_consumption_buffer_wh -= trade["energy"] * 1000
                    self.total_self_consumption_wh += trade["energy"] * 1000
                else:
                    self.total_self_consumption_wh += self.self_consumption_buffer_wh
                    self.self_consumption_buffer_wh = 0
            # self_consumption_buffer needs to be exhausted if sold to any external agent
            elif trade["buyer_origin_id"] not in [*self.ess_list, *self.consumer_list] and \
                    trade["buyer_origin_id"] == trade["buyer_id"] and \
                    self.self_consumption_buffer_wh > 0:
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
        if trade["seller_origin_id"] in self.buffer_list and \
                trade["buyer_origin_id"] in self.consumer_list and \
                trade["buyer_origin_id"] == trade["buyer_id"]:
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
        if trade["buyer_origin_id"] in self.buffer_list and \
                trade["seller_origin_id"] in self.producer_list \
                and trade["seller_origin_id"] == trade["seller_id"]:
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
    """Responsible for generating comparative savings from feed-in tariff vs D3A"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.producer_ess_set = set()  # keeps set of house's producing/ess devices
        self.consumer_ess_set = set()  # keeps set of house's consuming/ess devices
        self.fit_revenue = 0.  # revenue achieved by producing selling energy via FIT scheme
        self.utility_bill = 0.  # cost of energy purchase from energy supplier
        self.base_case_cost = 0.  # standard cost of a house participating in FIT scheme
        self.gsy_e_cost = 0.  # standard cost of a house participating in GSy Exchange
        self.saving_absolute = 0.  # savings achieved by a house via participating in D3A
        self.saving_percentage = 0.  # savings in percentage wrt FIT via participating in D3A

    def calculate_savings_kpi(self, area_dict: dict, core_stats: dict, gf_alp: float):
        """Calculates the referenced saving from feed-in tariff based participation vs D3A
        Args:
            area_dict: contain nested area info
            core_stats: contain area's raw/key statistics
            gf_alp: grid_fee_along_the_path - cumulative grid fee from root to target area

        """
        self.populate_consumer_producer_sets(area_dict)

        # fir_excl_gf_alp: feed-in tariff rate excluding grid fee along path
        fir_excl_gf_alp = self.get_feed_in_tariff_rate_excluding_path_grid_fees(
            core_stats.get(area_dict["uuid"], {}), gf_alp)
        # mmr_incl_gf_alp: market maker rate include grid fee along path
        mmr_incl_gf_alp = self.get_market_maker_rate_including_path_grid_fees(
            core_stats.get(area_dict["uuid"], {}), gf_alp)
        for trade in core_stats.get(area_dict["uuid"], {}).get("trades", []):
            if (trade["seller_origin_id"] in self.producer_ess_set and
                    trade["buyer_origin_id"] not in self.consumer_ess_set):
                self.fit_revenue += fir_excl_gf_alp * trade["energy"]
                self.gsy_e_cost -= trade["price"]
            if trade["buyer_origin_id"] in self.consumer_ess_set and \
                    trade["seller_origin_id"] not in self.producer_ess_set:
                self.utility_bill += mmr_incl_gf_alp * trade["energy"]
                self.gsy_e_cost += trade["price"]
        self.base_case_cost = self.utility_bill - self.fit_revenue
        self.saving_absolute = self.base_case_cost - self.gsy_e_cost
        self.saving_percentage = ((self.saving_absolute / self.base_case_cost) * 100
                                  if self.base_case_cost else 0.)

    def populate_consumer_producer_sets(self, area_dict: dict):
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
    def get_feed_in_tariff_rate_excluding_path_grid_fees(
            area_core_stat: dict, path_grid_fee: float):
        """
        Args:
            area_core_stat: It contains the respective area's core statistics
            path_grid_fee: Cumulative fee from root to target area
        Returns: feed-in tariff excluding accumulated grid fee from root to target area
        """
        return area_core_stat.get("feed_in_tariff", 0.) - path_grid_fee

    @staticmethod
    def get_market_maker_rate_including_path_grid_fees(
            area_core_stat: dict, path_grid_fee: float):
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
        return {"base_case_cost": self.base_case_cost,
                "utility_bill": self.utility_bill,
                "fit_revenue": self.fit_revenue,
                "gsy_e_cost": self.gsy_e_cost,
                "saving_absolute": self.saving_absolute,
                "saving_percentage": self.saving_percentage}


class KPI(ResultsBaseClass):
    """Placeholder for mapping respective area's KPI and SavingsKPI"""
    def __init__(self):
        self.performance_indices: Dict = {}
        self.performance_indices_redis: Dict = {}
        self.state: Dict = {}
        self.savings_state: Dict = {}  # keeps initialized savings kpi object for individual area

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

    def area_performance_indices(self, area_dict: Dict, core_stats: Dict) -> Dict:
        """Entrypoint to be triggered after every market cycle to calculate
        respective area's KPIs"""
        if area_dict["uuid"] not in self.state:
            self.state[area_dict["uuid"]] = KPIState()

        # initialization of house saving state
        if area_dict["uuid"] not in self.savings_state:
            if not has_grand_children(area_dict):
                self.savings_state[area_dict["uuid"]] = SavingsKPI()
        if area_dict["uuid"] in self.savings_state:
            self.savings_state[area_dict["uuid"]].calculate_savings_kpi(
                area_dict, core_stats, self.area_uuid_cum_grid_fee_mapping[area_dict["uuid"]])

        self.state[area_dict["uuid"]].accumulate_devices(area_dict)

        self.state[area_dict["uuid"]].update_area_kpi(area_dict, core_stats)
        self.state[area_dict["uuid"]].total_demand = (
                self.state[area_dict["uuid"]].total_energy_demanded_wh +
                self.state[area_dict["uuid"]].demanded_buffer_wh)

        # in case when the area doesn"t have any load demand
        if self.state[area_dict["uuid"]].total_demand <= 0:
            self_sufficiency = None
        elif (self.state[area_dict["uuid"]].total_self_consumption_wh >=
              self.state[area_dict["uuid"]].total_demand):
            self_sufficiency = 1.0
        else:
            self_sufficiency = (self.state[area_dict["uuid"]].total_self_consumption_wh /
                                self.state[area_dict["uuid"]].total_demand)

        if self.state[area_dict["uuid"]].total_energy_produced_wh <= 0:
            self_consumption = None
        elif (self.state[area_dict["uuid"]].total_self_consumption_wh >=
              self.state[area_dict["uuid"]].total_energy_produced_wh):
            self_consumption = 1.0
        else:
            self_consumption = (self.state[area_dict["uuid"]].total_self_consumption_wh /
                                self.state[area_dict["uuid"]].total_energy_produced_wh)

        kpi_parm_dict = {
            "self_sufficiency": self_sufficiency, "self_consumption": self_consumption,
            "total_energy_demanded_wh": self.state[area_dict["uuid"]].total_demand,
            "demanded_buffer_wh": self.state[area_dict["uuid"]].demanded_buffer_wh,
            "self_consumption_buffer_wh": self.state[area_dict["uuid"]].self_consumption_buffer_wh,
            "total_energy_produced_wh": self.state[area_dict["uuid"]].total_energy_produced_wh,
            "total_self_consumption_wh": self.state[area_dict["uuid"]].total_self_consumption_wh,
        }
        if self.savings_state.get(area_dict["uuid"]) is not None:
            kpi_parm_dict.update(self.savings_state[area_dict["uuid"]].to_dict())
        return kpi_parm_dict

    def _kpi_ratio_to_percentage(self, area_name: str):
        area_kpis = self.performance_indices[area_name]
        if area_kpis["self_sufficiency"] is not None:
            self_sufficiency_percentage = area_kpis["self_sufficiency"] * 100
        else:
            self_sufficiency_percentage = 0.0
        if area_kpis["self_consumption"] is not None:
            self_consumption_percentage = \
                area_kpis["self_consumption"] * 100
        else:
            self_consumption_percentage = 0.0

        return {"self_sufficiency": self_sufficiency_percentage,
                "self_consumption": self_consumption_percentage,
                "total_energy_demanded_wh": area_kpis["total_energy_demanded_wh"],
                "demanded_buffer_wh": area_kpis["demanded_buffer_wh"],
                "self_consumption_buffer_wh": area_kpis["self_consumption_buffer_wh"],
                "total_energy_produced_wh": area_kpis["total_energy_produced_wh"],
                "total_self_consumption_wh": area_kpis["total_self_consumption_wh"],
                "base_case_cost": area_kpis.get("base_case_cost"),
                "utility_bill": area_kpis.get("utility_bill"),
                "fit_revenue": area_kpis.get("fit_revenue"),
                "gsy_e_cost": area_kpis.get("gsy_e_cost"),
                "saving_absolute": area_kpis.get("saving_absolute"),
                "saving_percentage": area_kpis.get("saving_percentage")
                }

    # pylint: disable=arguments-renamed
    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str):
        """Entrypoint to iteratively updates all area's KPI"""
        if not self._has_update_parameters(area_dict, core_stats, current_market_slot):
            return

        self.area_uuid_cum_grid_fee_mapping[area_dict["uuid"]] = (
            self._accumulate_root_to_target_area_grid_fee(area_dict, core_stats))
        self.performance_indices[area_dict["uuid"]] = self.area_performance_indices(
            area_dict, core_stats)
        self.performance_indices_redis[area_dict["uuid"]] = self._kpi_ratio_to_percentage(
            area_dict["uuid"])

        for child in area_dict["children"]:
            if len(child["children"]) > 0:
                self.update(child, core_stats, current_market_slot)

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
            self.state[area_dict["uuid"]].self_consumption = \
                last_known_state_data["self_consumption"]
            self.state[area_dict["uuid"]].self_sufficiency = \
                last_known_state_data["self_sufficiency"]
            self.state[area_dict["uuid"]].demanded_buffer_wh = \
                last_known_state_data["demanded_buffer_wh"]
            self.state[area_dict["uuid"]].total_energy_demanded_wh = \
                last_known_state_data["total_energy_demanded_wh"]
            self.state[area_dict["uuid"]].total_energy_produced_wh = \
                last_known_state_data["total_energy_produced_wh"]
            self.state[area_dict["uuid"]].total_self_consumption_wh = \
                last_known_state_data["total_self_consumption_wh"]
            self.state[area_dict["uuid"]].self_consumption_buffer_wh = \
                last_known_state_data["self_consumption_buffer_wh"]
        if area_dict["uuid"] not in self.savings_state:
            if not has_grand_children(area_dict):
                self.savings_state[area_dict["uuid"]] = SavingsKPI()
                self.savings_state[area_dict["uuid"]].base_case_cost = (
                    last_known_state_data.get("base_case_cost", 0))
                self.savings_state[area_dict["uuid"]].utility_bill = (
                    last_known_state_data.get("utility_bill", 0))
                self.savings_state[area_dict["uuid"]].fit_revenue = (
                    last_known_state_data.get("fit_revenue", 0))
                self.savings_state[area_dict["uuid"]].gsy_e_cost = (
                    last_known_state_data.get("gsy_e_cost", 0)
                    or last_known_state_data.get("d3a_cost", 0))

    # pylint: disable=(arguments-differ
    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        raise NotImplementedError(
            "KPI endpoint supports only global results, merge not supported.")

    @property
    def raw_results(self):
        return self.performance_indices

    @property
    def ui_formatted_results(self):
        return self.performance_indices_redis
