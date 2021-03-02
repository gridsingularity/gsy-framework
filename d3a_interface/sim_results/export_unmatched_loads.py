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
from pendulum import duration
from itertools import product
from typing import Dict
from copy import deepcopy
from d3a_interface.constants_limits import GlobalConfig, FLOATING_POINT_TOLERANCE
from d3a_interface.sim_results import is_load_node_type
from d3a_interface.sim_results.results_abc import ResultsBaseClass


def get_number_of_unmatched_loads(indict):
    # use root dict:
    root = indict[list(indict.keys())[0]]
    no_ul = 0
    for parent in root.values():
        for value in parent['unmatched_loads'].values():
            no_ul += value['unmatched_count']
    return no_ul


class ExportUnmatchedLoads:
    def __init__(self):
        self.hour_list = self.hour_list()
        self.load_count = 0

    @staticmethod
    def hour_list():
        if GlobalConfig.sim_duration > duration(days=1):
            return [GlobalConfig.start_date.add(days=day, hours=hour)
                    for day, hour in product(range(GlobalConfig.sim_duration.days), range(24))]
        else:
            return [GlobalConfig.start_date.add(hours=hour) for hour in range(24)]

    def count_load_devices_in_setup(self, area):
        for child in area['children']:
            if is_load_node_type(child):
                self.load_count += 1
            if child['children']:
                self.count_load_devices_in_setup(child)

    def get_current_market_results(self, area_dict, core_stats, current_market_time_slot_str):
        unmatched_loads = self.expand_to_ul_to_hours(
                self.expand_ul_to_parents(
                    self.find_unmatched_loads(area_dict, core_stats, {},
                                              current_market_time_slot_str)[area_dict['name']],
                    area_dict['name'], {}
                ), current_market_time_slot_str)

        ul_uuid_as_key = {}
        ul_name_as_key = {}
        self.arrange_output_add_type(unmatched_loads, area_dict, ul_name_as_key)
        self.arrange_output_add_type(unmatched_loads, area_dict, ul_uuid_as_key, uuid_as_key=True)
        return ul_name_as_key, ul_uuid_as_key

    def find_unmatched_loads(self, area_dict, core_stats, indict, current_market_time_slot_str):
        """
        Aggregates list of times for each unmatched time slot for each load
        """
        indict[area_dict['name']] = {}
        for child in area_dict['children']:
            if child['children']:
                indict[area_dict['name']] = self.find_unmatched_loads(
                    child, core_stats, indict[area_dict['name']], current_market_time_slot_str
                )
            else:
                if is_load_node_type(child) and core_stats.get(child['uuid'], {}) != {}:
                    indict[area_dict['name']][child['name']] = \
                        self._calculate_unmatched_loads_leaf_area(child, core_stats,
                                                                  current_market_time_slot_str)
        return indict

    @classmethod
    def _calculate_unmatched_loads_leaf_area(cls, area_dict, core_stats,
                                             current_market_time_slot_str):
        """
        actually determines the unmatched loads
        """
        unmatched_times = []
        desired_energy_kWh = core_stats[area_dict['uuid']]['load_profile_kWh']
        traded_energy_kWh = sum(trade['energy']
                                for trade in core_stats[area_dict['uuid']]['trades'])
        deficit = desired_energy_kWh - traded_energy_kWh
        if deficit > FLOATING_POINT_TOLERANCE:
            unmatched_times.append(current_market_time_slot_str)
        return {"unmatched_times": unmatched_times}

    def _accumulate_all_uls_in_branch(self, subdict, unmatched_list) -> list:
        """
        aggregate all unmatched loads times in one branch into one list
        """
        for key in subdict.keys():
            if key == "unmatched_times":
                return unmatched_list + subdict[key]
            else:
                unmatched_list = self._accumulate_all_uls_in_branch(subdict[key], unmatched_list)
        return unmatched_list

    def expand_ul_to_parents(self, subdict, parent_name, outdict):
        """
        expand unmatched loads times to all nodes including all unmatched loads times of the
        sub branch
        """

        for node_name, subsubdict in subdict.items():
            if isinstance(subsubdict, dict):
                # nodes
                ul_list = self._accumulate_all_uls_in_branch(subsubdict, [])
                sub_ul = sorted(list(set(ul_list)))
                if parent_name in outdict:
                    outdict[parent_name].update({node_name: sub_ul})
                else:
                    outdict[parent_name] = {node_name: sub_ul}
                outdict.update(self.expand_ul_to_parents(subsubdict, node_name, {}))
            else:
                # leafs
                outdict[parent_name] = {parent_name: subsubdict}

        return outdict

    @classmethod
    def _get_hover_info(cls, indict, slot_time):
        """
        returns dict of UL for each subarea for the hover the UL graph
        """
        hover_dict = {}
        ul_count = 0
        for child_name, child_ul_list in indict.items():
            for time in child_ul_list:
                if time[11:13] == slot_time[11:13] and time[8:10] == slot_time[8:10] and \
                   time[5:7] == slot_time[5:7] and time[:4] == slot_time[:4]:
                    ul_count += 1
                    if child_name in hover_dict:
                        hover_dict[child_name].append(time)
                    else:
                        hover_dict[child_name] = [time]
        if hover_dict == {}:
            return {"unmatched_count": 0}
        else:
            return {"unmatched_count": ul_count, "unmatched_times": hover_dict}

    def expand_to_ul_to_hours(self, indict, current_market_time_slot_str):
        """
        Changing format to dict of hour time stamps
        """
        outdict = {}
        for node_name, subdict in indict.items():
            outdict[node_name] = {}
            outdict[node_name][current_market_time_slot_str] = \
                self._get_hover_info(subdict, current_market_time_slot_str)
        return outdict

    def arrange_output_add_type(self, indict, area_dict, outdict, uuid_as_key=False):
        if area_dict['children']:
            key = area_dict['uuid' if uuid_as_key else 'name']
            if key not in outdict:
                outdict[key] = {}
            for child in area_dict['children']:
                if child['children'] or is_load_node_type(child):
                    if child['name'] in indict:
                        if uuid_as_key:
                            outdict[area_dict['uuid']][child['name']] = \
                                {"unmatched_loads": indict[child['name']],
                                 "type": child["type"]}
                        else:
                            outdict[area_dict['name']][child['name']] = \
                                {"unmatched_loads": indict[child['name']],
                                 "type": child["type"]}
                    self.arrange_output_add_type(indict, child, outdict, uuid_as_key)


class MarketUnmatchedLoads(ResultsBaseClass):
    """
    This class is used for storing the current unmatched load results and to update them
    with new results whenever a market has been completed. It works in conjunction
    to the ExportUnmatchedLoads class, since it depends on the latter for calculating
    the unmatched loads for a market slot.
    """
    def __init__(self):
        self.unmatched_loads = {}
        self.last_unmatched_loads = {}
        self.export_unmatched_loads = ExportUnmatchedLoads()

    def write_none_to_unmatched_loads(self, area_dict):
        self.unmatched_loads[area_dict['name']] = None
        self.last_unmatched_loads[area_dict['uuid']] = None
        for child in area_dict['children']:
            self.write_none_to_unmatched_loads(child)

    def merge_unmatched_loads(self, current_results):
        """
        Merges unmatched loads for the last market to the global unmatched loads
        :param current_results: Output from ExportUnmatchedLoads.get_current_market_results()
        :param current_results_uuid: Output from ExportUnmatchedLoads.get_current_market_results()
        :return: Tuple with unmatched loads using area names and uuids
        """
        self.unmatched_loads = self.merge_results_to_global(
            current_results, self.unmatched_loads
        )

    def update(self, area_result_dict=None, core_stats=None, current_market_slot=None):
        if not self._has_update_parameters(
                area_result_dict, core_stats, current_market_slot):
            return

        self.export_unmatched_loads.count_load_devices_in_setup(area_result_dict)
        if self.export_unmatched_loads.load_count == 0:
            self.write_none_to_unmatched_loads(area_result_dict)
        else:
            current_results, current_results_uuid = \
                self.export_unmatched_loads.get_current_market_results(
                    area_result_dict, core_stats, current_market_slot
                )

            self.last_unmatched_loads = current_results_uuid
            self.merge_unmatched_loads(current_results)

    @staticmethod
    def merge_results_to_global(market_ul: Dict, global_ul: Dict, *_):
        if not global_ul:
            global_ul = market_ul
            return global_ul
        return UnmatchedLoadsHelpers.accumulate_current_market_results(global_ul, market_ul)

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        pass

    @property
    def raw_results(self):
        return self.unmatched_loads

    @property
    def ui_formatted_results(self):
        return self.last_unmatched_loads


class UnmatchedLoadsHelpers:

    @classmethod
    def _merge_base_area_unmatched_loads(cls, accumulated_results: Dict,
                                         current_results: Dict, area: str):
        """
        Recurses over all children (target areas) of base area and calculates the unmatched
        loads for each
        :param accumulated_results: stores the merged unmatched load results, changes by reference
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :param area: area of the accumulated unmatched loads
        :return: None
        """
        if area not in current_results or current_results[area] is None:
            accumulated_results[area] = None
            return
        for target, target_value in current_results[area].items():
            if accumulated_results[area] is None:
                accumulated_results[area] = {}
            if target not in accumulated_results[area]:
                accumulated_results[area][target] = deepcopy(target_value)
            else:
                if target == 'type':
                    continue
                elif target == 'unmatched_loads':
                    cls._copy_accumulated_unmatched_loads(
                        accumulated_results, current_results, area
                    )
                else:
                    cls._merge_target_area_unmatched_loads(
                        accumulated_results, current_results, area, target
                    )

    @classmethod
    def _merge_target_area_unmatched_loads(cls, accumulated_results: Dict,
                                           current_results: Dict, area: str, target: str):
        """
        Merges the unmatched loads and unmatched times for a base area and a target area.
        :param accumulated_results: stores the merged unmatched load results, changes by reference
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :param area: area of the accumulated unmatched loads
        :param target: target area of the accumulated unmatched loads
        :return: None
        """
        target_ul = accumulated_results[area][target]['unmatched_loads']
        current_ul = current_results[area][target]['unmatched_loads']
        for timestamp, ts_value in current_ul.items():
            if timestamp not in target_ul:
                target_ul[timestamp] = deepcopy(ts_value)
            else:
                if 'unmatched_times' not in current_ul[timestamp]:
                    continue
                if 'unmatched_times' not in target_ul[timestamp]:
                    target_ul[timestamp]['unmatched_times'] = {}
                for device, time_list in current_ul[timestamp]['unmatched_times'].items():
                    if device not in target_ul[timestamp]['unmatched_times']:
                        target_ul[timestamp]['unmatched_times'][device] = deepcopy(time_list)
                    else:
                        for ts in time_list:
                            if ts not in target_ul[timestamp]['unmatched_times'][device]:
                                target_ul[timestamp]['unmatched_times'][device].append(ts)

                unm_count = 0
                for _, hours in target_ul[timestamp]['unmatched_times'].items():
                    unm_count += len(hours)

                    target_ul[timestamp]['unmatched_count'] = unm_count

    @classmethod
    def _copy_accumulated_unmatched_loads(cls, accumulated_results: Dict,
                                          current_results: Dict, area: str):
        """
        Copies the accumulated results from the market results to the incremental results
        :param accumulated_results: stores the merged unmatched load results, changes by reference
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :param area: area of the accumulated unmatched loads
        :return: None
        """
        for timestamp, ts_value in current_results[area]['unmatched_loads'].items():
            if timestamp not in accumulated_results[area]['unmatched_loads']:
                accumulated_results[area]['unmatched_loads'][timestamp] = deepcopy(ts_value)

    @classmethod
    def accumulate_current_market_results(cls, accumulated_results: Dict, current_results: Dict):
        """
        Method which starts the merging of the current market unmatched loads with the
        existing unmatched loads (_unmatched_loads_incremental)
        :param accumulated_results: return value, stores the merged unmatched load results
        :param current_results: results for the current market, that are used to update the
        accumulated results
        :return: accumulated_results
        """
        for base_area, target_results in current_results.items():
            if base_area not in accumulated_results:
                accumulated_results[base_area] = deepcopy(target_results)
            else:
                cls._merge_base_area_unmatched_loads(
                    accumulated_results, current_results, base_area
                )
        return accumulated_results
