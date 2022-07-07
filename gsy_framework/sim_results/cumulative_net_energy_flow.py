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
from gsy_framework.utils import subtract_or_create_key, add_or_create_key, \
    area_bought_from_child, area_sells_to_child
from gsy_framework.sim_results.results_abc import ResultsBaseClass


class CumulativeNetEnergyFlow(ResultsBaseClass):
    def __init__(self):
        self.net_area_flow = {}

    def update(self, area_dict, core_stats, current_market_slot):
        if not self._has_update_parameters(
                area_dict, core_stats, current_market_slot):
            return
        self._update_results(area_dict, core_stats, current_market_slot)

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        area_uuid = area_dict["uuid"]
        # TODO: Restore the state only if it is a float. At the moment, the default value for
        # the DB column is an empty dict, which will be added for areas that do not support
        # the net energy flow. These need to be omitted from the state restore.
        # Needs to be refactored by changing the DB field from JSON to a float value,
        # and denote absence of the value by leaving the field empty.
        if area_uuid not in self.net_area_flow and \
                isinstance(last_known_state_data, float):
            self.net_area_flow[area_uuid] = last_known_state_data

    def _update_results(self, area_dict, core_stats, current_market_time_slot_str):
        self._accumulate_net_energy(area_dict, core_stats)
        for child in area_dict['children']:
            self._update_results(child, core_stats, current_market_time_slot_str)

    def _accumulate_net_energy(self, area_dict, core_stats):

        child_names = [c['name'] for c in area_dict['children']]
        for trade in self._get_trades_from_core_stats(core_stats, area_dict["uuid"]):
            if area_bought_from_child(trade, area_dict['name'], child_names):
                add_or_create_key(
                    self.net_area_flow, area_dict['uuid'], trade['energy']
                )
            # import
            if area_sells_to_child(trade, area_dict['name'], child_names):
                subtract_or_create_key(
                    self.net_area_flow, area_dict['uuid'], trade['energy']
                )

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        raise NotImplementedError(
            "Cumulative net energy flow endpoint supports only global results,"
            " merge not supported.")

    @property
    def raw_results(self):
        return self.net_area_flow

    def memory_allocation_size_kb(self):
        return 0.0
