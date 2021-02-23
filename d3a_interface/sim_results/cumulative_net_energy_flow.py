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
from d3a_interface.utils import subtract_or_create_key, add_or_create_key, \
    area_bought_from_child, area_sells_to_child


class CumulativeNetEnergyFlow:
    def __init__(self):
        self.net_area_flow = {}

    def update(self, area_dict, core_stats, current_market_time_slot_str):
        if current_market_time_slot_str == "":
            return
        self.update_results(area_dict, core_stats, current_market_time_slot_str)

    def update_results(self, area_dict, core_stats, current_market_time_slot_str):
        self._accumulate_net_energy(area_dict, core_stats)
        for child in area_dict['children']:
            self.update_results(child, core_stats, current_market_time_slot_str)

    def _accumulate_net_energy(self, area_dict, core_stats):

        child_names = [c['name'] for c in area_dict['children']]
        for trade in core_stats.get(area_dict['uuid'], {}).get('trades', []):
            if area_bought_from_child(trade, area_dict['name'], child_names):
                add_or_create_key(
                    self.net_area_flow, area_dict['uuid'], trade['energy']
                )
            # import
            if area_sells_to_child(trade, area_dict['name'], child_names):
                subtract_or_create_key(
                    self.net_area_flow, area_dict['uuid'], trade['energy']
                )
