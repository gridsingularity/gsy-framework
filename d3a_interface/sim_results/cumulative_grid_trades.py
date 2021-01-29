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
import ast

from d3a_interface.constants_limits import FLOATING_POINT_TOLERANCE
from d3a_interface.sim_results import is_load_node_type, \
    is_producer_node_type, is_prosumer_node_type, is_buffer_node_type, area_sells_to_child, \
    child_buys_from_area, area_name_from_area_or_iaa_name
from d3a_interface.utils import add_or_create_key, \
    make_iaa_name_from_dict, subtract_or_create_key, round_floats_for_ui, extract_number_from_list

accumulated_trades_default_dict = {
            "name": "",
            "type": "",
            "produced": 0.0,
            "earned": 0.0,
            "consumedFrom": {},
            "spentTo": {},
            "producedForExternal": {},
            "earnedFromExternal": {},
            "consumedFromExternal": {},
            "spentToExternal": {},
            "parent_uuid": "",
            "children": []
        }


class CumulativeGridTrades:
    def __init__(self):
        self.current_trades = {}
        self.current_balancing_trades = {}
        self.accumulated_trades = {}
        self.accumulated_balancing_trades = {}

    def update(self, area_dict, flattened_area_core_stats_dict):
        self.export_cumulative_grid_trades(
            area_dict, flattened_area_core_stats_dict, self.accumulated_trades
        )

    @classmethod
    def format_last_known_state(cls, area_uuid, last_known_state_data, area_name_uuid_map,
                                accumulated_trades={}):
        accumulated_trades[area_uuid] = accumulated_trades_default_dict
        accumulated_trades[area_uuid]['children'] = []
        accumulated_trades_map = {}
        for state_data in last_known_state_data:
            if state_data['areaName'] != 'External Trades':
                for data_list in state_data['bars']:
                    parsed_price = extract_number_from_list(data_list['priceLabel'])
                    if data_list['targetArea'] not in accumulated_trades_map:
                        accumulated_trades_map[data_list['targetArea']] = \
                            accumulated_trades_default_dict
                        accumulated_trades_map[data_list['targetArea']].update(
                            {'name': data_list['targetArea']}
                        )
                    # Producer entries
                    if "earned" in data_list['priceLabel'].split(" "):
                        accumulated_trades_map[data_list['targetArea']].update(
                            {'earned': parsed_price, 'produced': data_list['energy']}
                        )
                    # Consumer entries
                    elif "spent" in data_list['priceLabel'].split(" "):
                        accumulated_trades_map[data_list['targetArea']].update(
                            {'consumedFrom': {data_list['targetArea']: data_list['energy']},
                             'spentTo': {data_list['targetArea']: parsed_price}}
                        )
            else:
                for data_list in state_data['bars']:
                    parsed_price = extract_number_from_list(data_list['priceLabel'])
                    # Producer entries
                    if "earned" in data_list['priceLabel'].split(" "):
                        accumulated_trades[area_uuid].update(
                            {'earned': parsed_price, 'produced': data_list['energy']}
                        )
                    # Consumer entries
                    elif "spent" in data_list['priceLabel'].split(" "):
                        accumulated_trades[area_uuid]['consumedFrom'].update(
                            {data_list['targetArea']: data_list['energy']}
                        )
                        accumulated_trades[area_uuid]['spentTo'].update(
                            {data_list['targetArea']: parsed_price}
                        )
        for area_name, acc_data in accumulated_trades_map.items():
            accumulated_trades[area_uuid]['children'].append(
                {'name': area_name, 'uuid': area_name_uuid_map[area_name],
                 'accumulated_trades': acc_data}
            )
        return accumulated_trades

    def restore_area_results_state(self, area_uuid, last_known_state_data, area_name_uuid_map):
        if area_uuid not in self.accumulated_trades:
            if type(last_known_state_data) is list:
                last_known_state_data = self.format_last_known_state(
                    area_uuid, last_known_state_data, area_name_uuid_map
                )
            self.accumulated_trades[area_uuid] = last_known_state_data

    def export_cumulative_grid_trades(self, area_dict, flattened_area_core_stats_dict,
                                      accumulated_trades_redis):
        self.accumulated_trades = CumulativeGridTrades.accumulate_grid_trades_all_devices(
            area_dict, flattened_area_core_stats_dict, accumulated_trades_redis
        )

    @classmethod
    def accumulate_grid_trades_all_devices(cls, area_dict, flattened_area_core_stats_dict,
                                           accumulated_trades):
        for child_dict in area_dict['children']:
            if is_load_node_type(child_dict):
                accumulated_trades = CumulativeGridTrades._accumulate_load_trades(
                    child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades
                )
            if is_producer_node_type(child_dict):
                accumulated_trades = CumulativeGridTrades._accumulate_producer_trades(
                    child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades
                )
            elif is_prosumer_node_type(child_dict) or is_buffer_node_type(child_dict):
                accumulated_trades = \
                    CumulativeGridTrades._accumulate_storage_trade(
                        child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades
                    )

            elif child_dict['children'] == []:
                # Leaf node, no need for calculating cumulative trades, continue iteration
                continue
            else:
                accumulated_trades = cls.accumulate_grid_trades_all_devices(
                    child_dict, flattened_area_core_stats_dict, accumulated_trades
                )
                accumulated_trades = CumulativeGridTrades._accumulate_area_trades(
                    child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades
                )
        if area_dict['parent_uuid'] == "":
            accumulated_trades = CumulativeGridTrades._accumulate_area_trades(
                area_dict, {}, flattened_area_core_stats_dict, accumulated_trades
            )
        return accumulated_trades

    @classmethod
    def _accumulate_load_trades(cls, load, grid, flattened_area_core_stats_dict,
                                accumulated_trades):
        if load['uuid'] not in accumulated_trades:
            accumulated_trades[load['uuid']] = {
                "name": load['name'],
                "type": "load",
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "parent_uuid": load['parent_uuid'],
                "children": [{'name': child['name'], 'uuid': child['uuid']}
                             for child in load.get("children", [])]
            }

        area_trades = flattened_area_core_stats_dict.get(grid['uuid'], {}).get('trades', [])
        for trade in area_trades:
            if trade['buyer'] == load['name']:
                sell_id = area_name_from_area_or_iaa_name(trade['seller'])
                accumulated_trades[load['uuid']]["consumedFrom"] = add_or_create_key(
                    accumulated_trades[load['uuid']]["consumedFrom"], sell_id,
                    trade['energy'])
                accumulated_trades[load['uuid']]["spentTo"] = add_or_create_key(
                    accumulated_trades[load['uuid']]["spentTo"], sell_id,
                    (trade['energy'] * trade['energy_rate']))
        return accumulated_trades

    @classmethod
    def _accumulate_producer_trades(cls, producer, grid, flattened_area_core_stats_dict,
                                    accumulated_trades):
        if producer['uuid'] not in accumulated_trades:
            accumulated_trades[producer['uuid']] = {
                "name": producer['name'],
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "parent_uuid": producer['parent_uuid'],
                "children": [{'name': child['name'], 'uuid': child['uuid']}
                             for child in producer.get("children", [])]
            }

        area_trades = flattened_area_core_stats_dict.get(grid['uuid'], {}).get('trades', [])
        for trade in area_trades:
            if trade['seller'] == producer['name']:
                accumulated_trades[producer['uuid']]["produced"] -= trade['energy']
                accumulated_trades[producer['uuid']]["earned"] += \
                    (trade['energy_rate'] * trade['energy'])
        return accumulated_trades

    @classmethod
    def _accumulate_storage_trade(cls, storage, area, flattened_area_core_stats_dict,
                                  accumulated_trades):
        if storage['uuid'] not in accumulated_trades:
            accumulated_trades[storage['uuid']] = {
                "type": "Storage" if area['type'] == "StorageStrategy" else "InfiniteBus",
                "name": storage['name'],
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "parent_uuid": storage['parent_uuid'],
                "children": [{'name': child['name'], 'uuid': child['uuid']}
                             for child in storage.get("children", [])]
            }

        area_trades = flattened_area_core_stats_dict.get(area['uuid'], {}).get('trades', [])
        for trade in area_trades:
            if trade['buyer'] == storage['name']:
                sell_id = area_name_from_area_or_iaa_name(trade['seller'])
                accumulated_trades[storage['uuid']]["consumedFrom"] = add_or_create_key(
                    accumulated_trades[storage['uuid']]["consumedFrom"],
                    sell_id, trade['energy'])
                accumulated_trades[storage['uuid']]["spentTo"] = add_or_create_key(
                    accumulated_trades[storage['uuid']]["spentTo"], sell_id,
                    (trade['energy_rate'] * trade['energy']))
            elif trade['seller'] == storage['name']:
                accumulated_trades[storage['uuid']]["produced"] -= trade['energy']
                accumulated_trades[storage['uuid']]["earned"] += \
                    (trade['energy_rate'] * trade['energy'])
        return accumulated_trades

    @classmethod
    def _accumulate_area_trades(cls, area, parent, flattened_area_core_stats_dict,
                                accumulated_trades):
        if area['uuid'] not in accumulated_trades:
            accumulated_trades[area['uuid']] = {
                "name": area['name'],
                "type": "house",
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "producedForExternal": {},
                "earnedFromExternal": {},
                "consumedFromExternal": {},
                "spentToExternal": {},
                "parent_uuid": area['parent_uuid'],
                "children": [{'name': child['name'], 'uuid': child['uuid'],
                              'accumulated_trades': accumulated_trades.get(child['uuid'], {})}
                             for child in area.get("children", [])]
            }
        area_IAA_name = make_iaa_name_from_dict(area)
        child_names = [area_name_from_area_or_iaa_name(c['name']) for c in area['children']]
        area_trades = flattened_area_core_stats_dict.get(area['uuid'], {}).get('trades', [])

        for trade in area_trades:
            if area_name_from_area_or_iaa_name(trade['seller']) in child_names and \
                    area_name_from_area_or_iaa_name(trade['buyer']) in child_names:
                # House self-consumption trade
                accumulated_trades[area['uuid']]["produced"] -= trade['energy']
                accumulated_trades[area['uuid']]["earned"] += trade['price']
                accumulated_trades[area['uuid']]["consumedFrom"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["consumedFrom"],
                                      area['name'], trade['energy'])
                accumulated_trades[area['uuid']]["spentTo"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["spentTo"],
                                      area['name'], trade['price'])
            elif trade['buyer'] == area_IAA_name:
                accumulated_trades[area['uuid']]["earned"] += trade['price']
                accumulated_trades[area['uuid']]["produced"] -= trade['energy']
        # for market in area_markets:
        for trade in area_trades:
            if area_sells_to_child(trade, area['name'], child_names):
                accumulated_trades[area['uuid']]["consumedFromExternal"] = \
                    subtract_or_create_key(accumulated_trades[area['uuid']]
                                           ["consumedFromExternal"],
                                           area_name_from_area_or_iaa_name(trade['buyer']),
                                           trade['energy'])
                accumulated_trades[area['uuid']]["spentToExternal"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["spentToExternal"],
                                      area_name_from_area_or_iaa_name(trade['buyer']),
                                      trade['price'])
            elif child_buys_from_area(trade, area['name'], child_names):
                accumulated_trades[area['uuid']]["producedForExternal"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["producedForExternal"],
                                      area_name_from_area_or_iaa_name(trade['seller']),
                                      trade['energy'])
                accumulated_trades[area['uuid']]["earnedFromExternal"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["earnedFromExternal"],
                                      area_name_from_area_or_iaa_name(trade['seller']),
                                      trade['price'])

        accumulated_trades = CumulativeGridTrades._area_trade_from_parent(
            area, parent, flattened_area_core_stats_dict, accumulated_trades
        )

        return accumulated_trades

    @classmethod
    def _area_trade_from_parent(cls, area, parent, flattened_area_core_stats_dict,
                                accumulated_trades):
        if not parent:
            return accumulated_trades
        area_IAA_name = make_iaa_name_from_dict(area)
        parent_trades = flattened_area_core_stats_dict.get(parent['uuid'], {}).get('trades', [])

        for trade in parent_trades:
            if trade['buyer'] == area_IAA_name:
                seller_id = area_name_from_area_or_iaa_name(trade['seller'])
                accumulated_trades[area['uuid']]["consumedFrom"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["consumedFrom"],
                                      seller_id, trade['energy'])
                accumulated_trades[area['uuid']]["spentTo"] = \
                    add_or_create_key(accumulated_trades[area['uuid']]["spentTo"],
                                      seller_id, trade['price'])

        return accumulated_trades

    @classmethod
    def generate_area_cumulative_trade_redis(cls, child, parent_name, accumulated_trades):
        results = {"areaName": child['name']}
        area_data = accumulated_trades[child['uuid']]
        results["bars"] = []
        # Producer entries
        if abs(area_data["produced"]) > FLOATING_POINT_TOLERANCE:
            results["bars"].append(
                {"energy": round_floats_for_ui(area_data["produced"]), "targetArea": child['name'],
                 "energyLabel":
                     f"{child['name']} sold "
                     f"{str(round_floats_for_ui(abs(area_data['produced'])))} kWh",
                 "priceLabel":
                     f"{child['name']} earned "
                     f"{str(round_floats_for_ui(area_data['earned']))} cents"}
            )

        # Consumer entries
        for producer, energy in area_data["consumedFrom"].items():
            money = round_floats_for_ui(area_data["spentTo"][producer])
            tag = "external sources" if producer == parent_name else producer
            results["bars"].append({
                "energy": round_floats_for_ui(energy),
                "targetArea": producer,
                "energyLabel": f"{child['name']} bought "
                               f"{str(round_floats_for_ui(energy))} kWh from {tag}",
                "priceLabel": f"{child['name']} spent "
                              f"{str(round_floats_for_ui(money))} cents on energy from {tag}",
            })

        return results

    @classmethod
    def _external_trade_entries(cls, child_uuid, accumulated_trades):
        results = {"areaName": "External Trades"}
        area_data = accumulated_trades[child_uuid]
        if type(area_data) is str:
            area_data = ast.literal_eval(area_data)
        results["bars"] = []
        incoming_energy = 0
        spent = 0
        # External Trades entries
        if "consumedFromExternal" in area_data:
            for k, v in area_data["consumedFromExternal"].items():
                incoming_energy += round_floats_for_ui(area_data["consumedFromExternal"][k])
                spent += round_floats_for_ui(area_data["spentToExternal"][k])
                results["bars"].append({
                    "energy": incoming_energy,
                    "targetArea": area_data['name'],
                    "energyLabel": f"External sources sold "
                                   f"{abs(round_floats_for_ui(incoming_energy))} kWh",
                    "priceLabel": f"External sources "
                                  f"earned {abs(round_floats_for_ui(spent))} cents"

                })

        if "producedForExternal" in area_data:
            for k, v in area_data["producedForExternal"].items():
                outgoing_energy = round_floats_for_ui(area_data["producedForExternal"][k])
                earned = round_floats_for_ui(area_data["earnedFromExternal"][k])
                results["bars"].append({
                    "energy": outgoing_energy,
                    "targetArea": k,
                    "energyLabel": f"External sources bought {abs(outgoing_energy)} kWh "
                                   f"from {k}",
                    "priceLabel": f"{area_data['name']} spent {earned} cents."
                })
        return results

    @staticmethod
    def generate_cumulative_grid_trades_target_area(area_uuid, last_db_result):
        results = {area_uuid: []}

        if last_db_result is None or last_db_result.get('cumulative_grid_trades', None) is None:
            return {area_uuid: None}
        accumulated_trades = {area_uuid: last_db_result.get('cumulative_grid_trades', None)}
        if accumulated_trades is None:
            return results

        area_detail = accumulated_trades.get(area_uuid, {})
        if type(area_detail) is str:
            area_detail = ast.literal_eval(area_detail)
        if not area_detail:
            return results
        results[area_uuid] = []
        if type(area_detail) is list:
            # for an old format of accumulated trades
            return {area_uuid: area_detail}
        for child in area_detail.get('children', []):
            if child['accumulated_trades'] != {}:
                accumulated_trades[child['uuid']] = child['accumulated_trades']
                results[area_uuid].append(
                    CumulativeGridTrades.generate_area_cumulative_trade_redis(
                        child, area_detail['name'], accumulated_trades
                    ))

        if area_detail.get("parent_uuid", None) is not None:
            results[area_uuid].append(CumulativeGridTrades._external_trade_entries(
                area_uuid, accumulated_trades))
        return results
