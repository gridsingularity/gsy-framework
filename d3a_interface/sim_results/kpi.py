
"""
Copyright 2018 Grid Singularity
This file is part of D3A.

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
from d3a_interface.utils import if_not_in_list_append
from d3a_interface.sim_results import is_load_node_type, is_buffer_node_type, \
    is_prosumer_node_type, is_producer_node_type, has_no_grand_children
from d3a_interface.sim_results.results_abc import ResultsBaseClass


class KPIState:
    def __init__(self):
        self.producer_list = list()
        self.consumer_list = list()
        self.areas_to_trace_list = list()
        self.ess_list = list()
        self.buffer_list = list()
        self.total_energy_demanded_wh = 0
        self.demanded_buffer_wh = 0
        self.total_energy_produced_wh = 0
        self.total_self_consumption_wh = 0
        self.self_consumption_buffer_wh = 0

    def accumulate_devices(self, area_dict):
        for child in area_dict['children']:
            if is_producer_node_type(child):
                if_not_in_list_append(self.producer_list, child['uuid'])
                if_not_in_list_append(self.areas_to_trace_list, child['parent_uuid'])
            elif is_load_node_type(child):
                if_not_in_list_append(self.consumer_list, child['uuid'])
                if_not_in_list_append(self.areas_to_trace_list, child['parent_uuid'])
            elif is_prosumer_node_type(child):
                if_not_in_list_append(self.ess_list, child['uuid'])
            elif is_buffer_node_type(child):
                if_not_in_list_append(self.buffer_list, child['uuid'])
            if child['children']:
                self.accumulate_devices(child)

    def _accumulate_total_energy_demanded(self, area_dict, core_stats):
        for child in area_dict['children']:
            child_stats = core_stats.get(child['uuid'], {})
            if is_load_node_type(child):
                self.total_energy_demanded_wh += child_stats.get('total_energy_demanded_wh', 0)
            if child['children']:
                self._accumulate_total_energy_demanded(child, core_stats)

    def _accumulate_self_production(self, trade):
        # Trade seller_id origin should be equal to the trade seller_id in order to
        # not double count trades in higher hierarchies
        if trade['seller_origin_id'] in self.producer_list and \
                trade['seller_origin_id'] == trade['seller_id']:
            self.total_energy_produced_wh += trade['energy'] * 1000

    def _accumulate_self_consumption(self, trade):
        # Trade buyer_id origin should be equal to the trade buyer_id in order to
        # not double count trades in higher hierarchies
        if trade['seller_origin_id'] in self.producer_list and \
                trade['buyer_origin_id'] in self.consumer_list and \
                trade['buyer_origin_id'] == trade['buyer_id']:
            self.total_self_consumption_wh += trade['energy'] * 1000

    def _accumulate_self_consumption_buffer(self, trade):
        if trade['seller_origin_id'] in self.producer_list and \
                trade['buyer_origin_id'] in self.ess_list:
            self.self_consumption_buffer_wh += trade['energy'] * 1000

    def _dissipate_self_consumption_buffer(self, trade):
        if trade['seller_origin_id'] in self.ess_list:
            # self_consumption_buffer needs to be exhausted to total_self_consumption
            # if sold to internal consumer
            if trade['buyer_origin_id'] in self.consumer_list and \
                    trade['buyer_origin_id'] == trade['buyer_id'] and \
                    self.self_consumption_buffer_wh > 0:
                if (self.self_consumption_buffer_wh - trade['energy'] * 1000) > 0:
                    self.self_consumption_buffer_wh -= trade['energy'] * 1000
                    self.total_self_consumption_wh += trade['energy'] * 1000
                else:
                    self.total_self_consumption_wh += self.self_consumption_buffer_wh
                    self.self_consumption_buffer_wh = 0
            # self_consumption_buffer needs to be exhausted if sold to any external agent
            elif trade['buyer_origin_id'] not in [*self.ess_list, *self.consumer_list] and \
                    trade['buyer_origin_id'] == trade['buyer_id'] and \
                    self.self_consumption_buffer_wh > 0:
                if (self.self_consumption_buffer_wh - trade['energy'] * 1000) > 0:
                    self.self_consumption_buffer_wh -= trade['energy'] * 1000
                else:
                    self.self_consumption_buffer_wh = 0

    def _accumulate_infinite_consumption(self, trade):
        """
        If the InfiniteBus is a seller_id of the trade when below the referenced area and bought
        by any of child devices.
        * total_self_consumption_wh needs to accumulated.
        * total_energy_produced_wh also needs to accumulated accounting of what
        the InfiniteBus has produced.
        """
        if trade['seller_origin_id'] in self.buffer_list and \
                trade['buyer_origin_id'] in self.consumer_list and \
                trade['buyer_origin_id'] == trade['buyer_id']:
            self.total_self_consumption_wh += trade['energy'] * 1000
            self.total_energy_produced_wh += trade['energy'] * 1000

    def _dissipate_infinite_consumption(self, trade):
        """
        If the InfiniteBus is a buyer_id of the trade when below the referenced area
        and sold by any of child devices.
        total_self_consumption_wh needs to accumulated.
        demanded_buffer_wh also needs to accumulated accounting of what
        the InfiniteBus has consumed/demanded.
        """
        if trade['buyer_origin_id'] in self.buffer_list and \
                trade['seller_origin_id'] in self.producer_list \
                and trade['seller_origin_id'] == trade['seller_id']:
            self.total_self_consumption_wh += trade['energy'] * 1000
            self.demanded_buffer_wh += trade['energy'] * 1000

    def _accumulate_energy_trace(self, core_stats):
        for target_area_uuid in self.areas_to_trace_list:
            target_core_stats = core_stats.get(target_area_uuid, {})
            for trade in target_core_stats.get('trades', []):
                self._accumulate_self_consumption(trade)
                self._accumulate_self_production(trade)
                self._accumulate_self_consumption_buffer(trade)
                self._dissipate_self_consumption_buffer(trade)
                self._accumulate_infinite_consumption(trade)
                self._dissipate_infinite_consumption(trade)

    def update_area_kpi(self, area_dict, core_stats):
        self.total_energy_demanded_wh = 0
        self._accumulate_total_energy_demanded(area_dict, core_stats)
        self._accumulate_energy_trace(core_stats)


class SavingKPI:
    def __init__(self):
        self.producer_list = list()
        self.consumer_list = list()
        self.ess_list = list()
        self.house_list = list()
        self.fit_revenue = 0.
        self.utility_bill = 0.
        self.d3a_revenue = 0.
        self.saving_absolute = 0.
        self.saving_percentage = 0.

    def calculate_saving_kpi(self, area_dict, core_stats, gf_alp):
        """
        :param area_dict: contain nested area info
        :param core_stats: contain area's raw/key statistics
        :param gf_alp: grid_fee_along_the_path - cumulative grid fee from root to target area
        :return:
        """
        for child in area_dict['children']:
            if is_producer_node_type(child):
                if_not_in_list_append(self.producer_list, child['uuid'])
            elif is_load_node_type(child):
                if_not_in_list_append(self.consumer_list, child['uuid'])
            elif is_prosumer_node_type(child):
                if_not_in_list_append(self.ess_list, child['uuid'])

        # fir_excl_gf_alp: feed-in tariff rate excluding grid fee along path
        fir_excl_gf_alp = (core_stats.get(area_dict['uuid'], {}).get('feed_in_tariff', 0.) -
                           gf_alp)
        # mmr_incl_gf_alp: market maker rate include grid fee along path
        mmr_incl_gf_alp = (core_stats.get(area_dict['uuid'], {}).get('market_maker_rate', 0.) +
                           gf_alp)
        for trade in core_stats.get(area_dict['uuid'], {}).get('trades', []):
            if trade['seller_origin_id'] in [self.producer_list, self.ess_list]:
                self.fit_revenue += fir_excl_gf_alp * trade['energy']
                self.d3a_revenue += trade['rate'] * trade['energy']
            if trade['buyer_origin_id'] in [self.consumer_list, self.ess_list]:
                self.utility_bill += mmr_incl_gf_alp * trade['energy']
                self.d3a_revenue -= trade['rate'] * trade['energy']
        base_case_revenue = self.fit_revenue + self.utility_bill
        self.saving_absolute = self.d3a_revenue - base_case_revenue
        self.saving_percentage = ((self.saving_absolute / base_case_revenue) * 100
                                  if base_case_revenue != 0 else 0.)


class KPI(ResultsBaseClass):
    def __init__(self):
        self.performance_indices = dict()
        self.performance_indices_redis = dict()
        self.state = {}
        self.saving_state = {}
        self.area_uuid_to_cum_fee_path = {}

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([
            self.performance_indices, self.performance_indices_redis
        ])

    def __repr__(self):
        return f"KPI: {self.performance_indices}"

    def area_performance_indices(self, area_dict, core_stats):
        if area_dict['uuid'] not in self.state:
            self.state[area_dict['uuid']] = KPIState()

        # initialization of house saving state
        if area_dict['uuid'] not in self.saving_state and has_no_grand_children(area_dict):
            self.saving_state[area_dict['uuid']] = SavingKPI()
        if area_dict['uuid'] in self.saving_state:
            self.saving_state[area_dict['uuid']].calculate_saving_kpi(
                area_dict, core_stats, self.area_uuid_to_cum_fee_path[area_dict['uuid']])

        self.state[area_dict['uuid']].accumulate_devices(area_dict)

        self.state[area_dict['uuid']].update_area_kpi(area_dict, core_stats)
        self.state[area_dict['uuid']].total_demand = (
                self.state[area_dict['uuid']].total_energy_demanded_wh +
                self.state[area_dict['uuid']].demanded_buffer_wh)

        # in case when the area doesn't have any load demand
        if self.state[area_dict['uuid']].total_demand <= 0:
            self_sufficiency = None
        elif (self.state[area_dict['uuid']].total_self_consumption_wh >=
              self.state[area_dict['uuid']].total_demand):
            self_sufficiency = 1.0
        else:
            self_sufficiency = (self.state[area_dict['uuid']].total_self_consumption_wh /
                                self.state[area_dict['uuid']].total_demand)

        if self.state[area_dict['uuid']].total_energy_produced_wh <= 0:
            self_consumption = None
        elif (self.state[area_dict['uuid']].total_self_consumption_wh >=
              self.state[area_dict['uuid']].total_energy_produced_wh):
            self_consumption = 1.0
        else:
            self_consumption = (self.state[area_dict['uuid']].total_self_consumption_wh /
                                self.state[area_dict['uuid']].total_energy_produced_wh)
        return {
            "self_sufficiency": self_sufficiency, "self_consumption": self_consumption,
            "total_energy_demanded_wh": self.state[area_dict['uuid']].total_demand,
            "demanded_buffer_wh": self.state[area_dict['uuid']].demanded_buffer_wh,
            "self_consumption_buffer_wh": self.state[area_dict['uuid']].self_consumption_buffer_wh,
            "total_energy_produced_wh": self.state[area_dict['uuid']].total_energy_produced_wh,
            "total_self_consumption_wh":
                self.state[area_dict['uuid']].total_self_consumption_wh,
            "saving_absolute": getattr(self.saving_state.get(area_dict['uuid'], None),
                                       'saving_absolute', None),
            "saving_percentage": getattr(self.saving_state.get(area_dict['uuid'], None),
                                         'saving_percentage', None)
        }

    def _kpi_ratio_to_percentage(self, area_name):
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
                "demanded_buffer_wh": area_kpis['demanded_buffer_wh'],
                "self_consumption_buffer_wh": area_kpis['self_consumption_buffer_wh'],
                "total_energy_produced_wh": area_kpis["total_energy_produced_wh"],
                "total_self_consumption_wh": area_kpis["total_self_consumption_wh"]
                }

    def update(self, area_dict, core_stats, current_market_slot):
        if not self._has_update_parameters(area_dict, core_stats, current_market_slot):
            return

        parent_fee = self.area_uuid_to_cum_fee_path.get(area_dict.get('parent_uuid', ''), 0.)
        area_fee = core_stats.get(area_dict.get('uuid', ''), {}).get('const_fee_rate', 0.)
        self.area_uuid_to_cum_fee_path[area_dict['uuid']] = parent_fee + area_fee

        self.performance_indices[area_dict['uuid']] = \
            self.area_performance_indices(area_dict, core_stats)
        self.performance_indices_redis[area_dict['uuid']] = \
            self._kpi_ratio_to_percentage(area_dict['uuid'])

        for child in area_dict['children']:
            if len(child['children']) > 0:
                self.update(child, core_stats, current_market_slot)

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        if not last_known_state_data:
            return
        if area_dict['uuid'] not in self.state:
            self.state[area_dict['uuid']] = KPIState()
            self.state[area_dict['uuid']].self_consumption = \
                last_known_state_data['self_consumption']
            self.state[area_dict['uuid']].self_sufficiency = \
                last_known_state_data['self_sufficiency']
            self.state[area_dict['uuid']].demanded_buffer_wh = \
                last_known_state_data['demanded_buffer_wh']
            self.state[area_dict['uuid']].total_energy_demanded_wh = \
                last_known_state_data['total_energy_demanded_wh']
            self.state[area_dict['uuid']].total_energy_produced_wh = \
                last_known_state_data['total_energy_produced_wh']
            self.state[area_dict['uuid']].total_self_consumption_wh = \
                last_known_state_data['total_self_consumption_wh']
            self.state[area_dict['uuid']].self_consumption_buffer_wh = \
                last_known_state_data['self_consumption_buffer_wh']

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
