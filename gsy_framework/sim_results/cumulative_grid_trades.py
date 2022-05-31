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
import ast
from typing import Dict

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE
from gsy_framework.sim_results import (
    is_load_node_type, is_producer_node_type, is_prosumer_node_type, is_buffer_node_type,
    area_sells_to_child, child_buys_from_area)
from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import (
    add_or_create_key, area_name_from_area_or_ma_name, subtract_or_create_key, round_floats_for_ui)


class CumulativeGridTrades(ResultsBaseClass):
    """Handle cumulative grid trades results."""

    def __init__(self):
        self.current_trades = {}
        self.current_balancing_trades = {}
        self.accumulated_trades = {}
        self.accumulated_balancing_trades = {}
        self._restored = False

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([
            self.current_trades, self.current_balancing_trades, self.accumulated_trades,
            self.accumulated_balancing_trades
        ])

    def update(self, area_dict, core_stats, current_market_slot):
        # pylint: disable=arguments-renamed
        if not self._has_update_parameters(
                area_dict, core_stats, current_market_slot):
            return
        self._export_cumulative_grid_trades(
            area_dict, core_stats, self.accumulated_trades
        )
        self._restored = False

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        self._restored = True
        if area_dict["uuid"] not in self.accumulated_trades:
            self.accumulated_trades[area_dict["uuid"]] = last_known_state_data

    def _export_cumulative_grid_trades(self, area_dict, flattened_area_core_stats_dict,
                                       accumulated_trades_redis):
        self.accumulated_trades = self._accumulate_grid_trades_all_devices(
            area_dict, flattened_area_core_stats_dict, accumulated_trades_redis
        )

    def _accumulate_grid_trades_all_devices(self, area_dict, flattened_area_core_stats_dict,
                                            accumulated_trades):
        for child_dict in area_dict["children"]:
            if is_load_node_type(child_dict):
                accumulated_trades = self._accumulate_load_trades(
                    child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades
                )
            if is_producer_node_type(child_dict):
                accumulated_trades = self._accumulate_producer_trades(
                    child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades
                )
            elif is_prosumer_node_type(child_dict) or is_buffer_node_type(child_dict):
                accumulated_trades = (self._accumulate_storage_trade(
                        child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades))
            elif not child_dict["children"]:
                # Leaf node, no need for calculating cumulative trades, continue iteration
                continue
            else:
                accumulated_trades = self._accumulate_grid_trades_all_devices(
                    child_dict, flattened_area_core_stats_dict, accumulated_trades)
                accumulated_trades = self._accumulate_area_trades(
                    child_dict, area_dict, flattened_area_core_stats_dict, accumulated_trades)
        if area_dict["parent_uuid"] == "":
            accumulated_trades = self._accumulate_area_trades(
                area_dict, {}, flattened_area_core_stats_dict, accumulated_trades)
        return accumulated_trades

    @staticmethod
    def _accumulate_load_trades(load, grid, flattened_area_core_stats_dict, accumulated_trades):
        if load["uuid"] not in accumulated_trades:
            accumulated_trades[load["uuid"]] = {
                "name": load["name"],
                "type": "load",
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "parent_uuid": load["parent_uuid"],
                "children": [{"name": child["name"], "uuid": child["uuid"]}
                             for child in load.get("children", [])]
            }

        area_trades = flattened_area_core_stats_dict.get(grid["uuid"], {}).get("trades", [])
        for trade in area_trades:
            if trade["buyer"] == load["name"]:
                sell_id = area_name_from_area_or_ma_name(trade["seller"])
                accumulated_trades[load["uuid"]]["consumedFrom"] = add_or_create_key(
                    accumulated_trades[load["uuid"]]["consumedFrom"], sell_id,
                    trade["energy"])
                accumulated_trades[load["uuid"]]["spentTo"] = add_or_create_key(
                    accumulated_trades[load["uuid"]]["spentTo"], sell_id,
                    (trade["energy"] * trade["energy_rate"]))
        return accumulated_trades

    @staticmethod
    def _accumulate_producer_trades(producer, grid, flattened_area_core_stats_dict,
                                    accumulated_trades):
        if producer["uuid"] not in accumulated_trades:
            accumulated_trades[producer["uuid"]] = {
                "name": producer["name"],
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "parent_uuid": producer["parent_uuid"],
                "children": [{"name": child["name"], "uuid": child["uuid"]}
                             for child in producer.get("children", [])]
            }

        area_trades = flattened_area_core_stats_dict.get(grid["uuid"], {}).get("trades", [])
        for trade in area_trades:
            if trade["seller"] == producer["name"]:
                accumulated_trades[producer["uuid"]]["produced"] -= trade["energy"]
                accumulated_trades[producer["uuid"]]["earned"] += (
                        trade["energy_rate"] * trade["energy"])
        return accumulated_trades

    @staticmethod
    def _accumulate_storage_trade(storage, area, flattened_area_core_stats_dict,
                                  accumulated_trades):
        if storage["uuid"] not in accumulated_trades:
            accumulated_trades[storage["uuid"]] = {
                "type": "Storage" if area["type"] == "StorageStrategy" else "InfiniteBus",
                "name": storage["name"],
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "parent_uuid": storage["parent_uuid"],
                "children": [{"name": child["name"], "uuid": child["uuid"]}
                             for child in storage.get("children", [])]
            }

        area_trades = flattened_area_core_stats_dict.get(area["uuid"], {}).get("trades", [])
        for trade in area_trades:
            if trade["buyer"] == storage["name"]:
                sell_id = area_name_from_area_or_ma_name(trade["seller"])
                accumulated_trades[storage["uuid"]]["consumedFrom"] = add_or_create_key(
                    accumulated_trades[storage["uuid"]]["consumedFrom"],
                    sell_id, trade["energy"])
                accumulated_trades[storage["uuid"]]["spentTo"] = add_or_create_key(
                    accumulated_trades[storage["uuid"]]["spentTo"], sell_id,
                    (trade["energy_rate"] * trade["energy"]))
            elif trade["seller"] == storage["name"]:
                accumulated_trades[storage["uuid"]]["produced"] -= trade["energy"]
                accumulated_trades[storage["uuid"]]["earned"] += (
                        trade["energy_rate"] * trade["energy"])
        return accumulated_trades

    @staticmethod
    def _generate_accumulated_trades_child_dict(accumulated_trades, child):
        return {
            "name": child["name"], "uuid": child["uuid"],
            "accumulated_trades": accumulated_trades.get(child["uuid"], {})
        }

    def _update_area_children_in_accumulated_trades_dict(self, accumulated_trades, area):
        """
        Updating current accumulated trades dynamically with children that might have been
        created after the simulation has started, via live events. We need to read again the
        child list from the accumulated trades and see if it matches with the
        Args:
            accumulated_trades: dict that stores the accumulated trades. Its value is changed
                                by reference in the method.
            area: area dict that includes children
        Returns: None
        """
        current_child_uuids = [
            child["uuid"] for child in accumulated_trades[area["uuid"]].get("children") or []
        ]
        for child in area.get("children", []):
            if child["uuid"] not in current_child_uuids:
                accumulated_trades[area["uuid"]]["children"].append(
                    self._generate_accumulated_trades_child_dict(
                        accumulated_trades, child
                    )
                )
            if self._restored:
                try:
                    child_index = current_child_uuids.index(child["uuid"])
                    accumulated_trades[area["uuid"]]["children"][child_index] = (
                        self._generate_accumulated_trades_child_dict(
                            accumulated_trades, child
                        ))
                except ValueError:
                    pass

    def _accumulate_area_trades(self, area, parent, flattened_area_core_stats_dict,
                                accumulated_trades):
        if area["uuid"] not in accumulated_trades:
            accumulated_trades[area["uuid"]] = {
                "name": area["name"],
                "type": "house",
                "produced": 0.0,
                "earned": 0.0,
                "consumedFrom": {},
                "spentTo": {},
                "producedForExternal": {},
                "earnedFromExternal": {},
                "consumedFromExternal": {},
                "spentToExternal": {},
                "parent_uuid": area["parent_uuid"],
                "children": [
                    self._generate_accumulated_trades_child_dict(
                        accumulated_trades, child
                    )
                    for child in area.get("children", [])
                ]
            }

        self._update_area_children_in_accumulated_trades_dict(accumulated_trades, area)

        child_names = [area_name_from_area_or_ma_name(c["name"]) for c in area["children"]]
        area_trades = flattened_area_core_stats_dict.get(area["uuid"], {}).get("trades", [])

        for trade in area_trades:
            if (area_name_from_area_or_ma_name(trade["seller"]) in child_names and
                    area_name_from_area_or_ma_name(trade["buyer"]) in child_names):
                # House self-consumption trade
                accumulated_trades[area["uuid"]]["produced"] -= trade["energy"]
                accumulated_trades[area["uuid"]]["earned"] += trade["price"]
                accumulated_trades[area["uuid"]]["consumedFrom"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["consumedFrom"],
                                      area["name"], trade["energy"]))
                accumulated_trades[area["uuid"]]["spentTo"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["spentTo"],
                                      area["name"], trade["price"]))
            elif trade["buyer"] == area["name"]:
                accumulated_trades[area["uuid"]]["earned"] += trade["price"]
                accumulated_trades[area["uuid"]]["produced"] -= trade["energy"]
        # for market in area_markets:
        for trade in area_trades:
            if area_sells_to_child(trade, area["name"], child_names):
                accumulated_trades[area["uuid"]]["consumedFromExternal"] = (
                    subtract_or_create_key(accumulated_trades[area["uuid"]]
                                           ["consumedFromExternal"],
                                           area_name_from_area_or_ma_name(trade["buyer"]),
                                           trade["energy"]))
                accumulated_trades[area["uuid"]]["spentToExternal"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["spentToExternal"],
                                      area_name_from_area_or_ma_name(trade["buyer"]),
                                      trade["price"]))
            elif child_buys_from_area(trade, area["name"], child_names):
                accumulated_trades[area["uuid"]]["producedForExternal"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["producedForExternal"],
                                      area_name_from_area_or_ma_name(trade["seller"]),
                                      trade["energy"]))
                accumulated_trades[area["uuid"]]["earnedFromExternal"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["earnedFromExternal"],
                                      area_name_from_area_or_ma_name(trade["seller"]),
                                      trade["price"]))

        accumulated_trades = self._area_trade_from_parent(
            area, parent, flattened_area_core_stats_dict, accumulated_trades
        )

        return accumulated_trades

    @staticmethod
    def _area_trade_from_parent(area, parent, flattened_area_core_stats_dict,
                                accumulated_trades):
        if not parent:
            return accumulated_trades
        parent_trades = flattened_area_core_stats_dict.get(parent["uuid"], {}).get("trades", [])

        for trade in parent_trades:
            if trade["buyer"] == area["name"]:
                seller_id = area_name_from_area_or_ma_name(trade["seller"])
                accumulated_trades[area["uuid"]]["consumedFrom"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["consumedFrom"],
                                      seller_id, trade["energy"]))
                accumulated_trades[area["uuid"]]["spentTo"] = (
                    add_or_create_key(accumulated_trades[area["uuid"]]["spentTo"],
                                      seller_id, trade["price"]))

        return accumulated_trades

    @staticmethod
    def _generate_area_cumulative_trade_redis(child, accumulated_trades):
        results = {"areaName": child["name"]}
        area_data = accumulated_trades[child["uuid"]]
        results["bars"] = []
        # Producer entries
        if abs(area_data["produced"]) > FLOATING_POINT_TOLERANCE:
            results["bars"].append(
                {"energy": round_floats_for_ui(area_data["produced"]), "targetArea": child["name"]}
            )

        # Consumer entries
        for producer, energy in area_data["consumedFrom"].items():
            results["bars"].append({
                "energy": round_floats_for_ui(energy),
                "targetArea": producer
            })

        return results

    @staticmethod
    def _external_trade_entries(child_uuid, accumulated_trades):
        results = {"areaName": "External Trades"}
        area_data = accumulated_trades[child_uuid]
        if isinstance(area_data, str):
            area_data = ast.literal_eval(area_data)
        results["bars"] = []
        incoming_energy = 0
        spent = 0
        if "consumedFromExternal" in area_data:
            for area_name, consumed_energy in area_data["consumedFromExternal"].items():
                incoming_energy += round_floats_for_ui(consumed_energy)
                spent += round_floats_for_ui(area_data["spentToExternal"][area_name])
                results["bars"].append({
                    "energy": incoming_energy,
                    "targetArea": area_data["name"]
                })
        if "producedForExternal" in area_data:
            for area_name, produced_energy in area_data["producedForExternal"].items():
                outgoing_energy = round_floats_for_ui(produced_energy)
                results["bars"].append({
                    "energy": outgoing_energy,
                    "targetArea": area_name
                })
        return results

    @classmethod
    def generate_cumulative_grid_trades_target_area(cls, area_uuid, last_db_result):
        """Generate the cumulative grid trades structure for target area with area_uuid"""
        results = {area_uuid: []}
        if last_db_result is None or last_db_result.get("cumulative_grid_trades", None) is None:
            return {area_uuid: None}
        accumulated_trades = {area_uuid: last_db_result.get("cumulative_grid_trades", None)}
        if accumulated_trades is None:
            return results

        area_detail = accumulated_trades.get(area_uuid, {})
        if isinstance(area_detail, str):
            area_detail = ast.literal_eval(area_detail)
        if not area_detail:
            return results
        results[area_uuid] = []
        if isinstance(area_detail, list):
            return {area_uuid: area_detail}
        for child in area_detail.get("children", []):
            if child["accumulated_trades"] != {}:
                accumulated_trades[child["uuid"]] = child["accumulated_trades"]
                results[area_uuid].append(
                    cls._generate_area_cumulative_trade_redis(
                        child, accumulated_trades
                    ))

        if area_detail.get("parent_uuid", None) is not None:
            results[area_uuid].append(cls._external_trade_entries(
                area_uuid, accumulated_trades))
        return results

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        # pylint: disable=arguments-differ
        raise NotImplementedError(
            "Cumulative grid trades endpoint supports only global results,"
            " merge not supported.")

    @property
    def raw_results(self):
        return self.accumulated_trades
