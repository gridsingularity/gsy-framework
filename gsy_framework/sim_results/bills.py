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
from copy import copy, deepcopy
from typing import Dict

from gsy_framework.constants_limits import ConstSettings
from gsy_framework.sim_results import (
    get_unified_area_type, is_load_node_type, is_pv_node_type)
from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import (
    area_name_from_area_or_ma_name, get_area_uuid_name_mapping, key_in_dict_and_not_none,
    round_floats_for_ui)


# pylint: disable=arguments-renamed
class CumulativeBills(ResultsBaseClass):
    """Class to compute the cumulative bills of a market."""

    def __init__(self):
        self.cumulative_bills_results = {}

    @classmethod
    def _calculate_device_penalties(cls, area, area_core_stats):
        if "children" in area and (len(area["children"]) > 0 or area_core_stats == {}):
            return 0.0

        if is_load_node_type(area):
            return area_core_stats["energy_requirement_kWh"]
        if is_pv_node_type(area):
            return area_core_stats["available_energy_kWh"]

        return 0.0

    @property
    def cumulative_bills(self):
        """Return the computed cumulative bills."""
        return {
            uuid: {
                "name": results["name"],
                "spent_total": round_floats_for_ui(results["spent_total"]),
                "earned": round_floats_for_ui(results["earned"]),
                "penalties": round_floats_for_ui(results["penalties"]),
                "penalty_energy": round_floats_for_ui(results["penalty_energy"]),
                "total": round_floats_for_ui(results["total"])
            }
            for uuid, results in self.cumulative_bills_results.items()
        }

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """Add the existing results of an area to the cumulative bills' results."""
        if not last_known_state_data:
            return
        if area_dict["uuid"] not in self.cumulative_bills_results:
            self.cumulative_bills_results[area_dict["uuid"]] = {
                "name": last_known_state_data["name"],
                "spent_total": last_known_state_data["spent_total"],
                "earned": last_known_state_data["earned"],
                "penalties": last_known_state_data["penalties"],
                "penalty_energy": last_known_state_data["penalty_energy"],
                "total": last_known_state_data["total"],
            }

    def update(self, area_dict=None, core_stats=None, current_market_slot=None):
        if not self._has_update_parameters(
                area_dict, core_stats, current_market_slot):
            return
        if area_dict.get("children"):
            for child in area_dict["children"]:
                self.update(child, core_stats, current_market_slot)

        if area_dict["uuid"] not in self.cumulative_bills_results:
            self.cumulative_bills_results[area_dict["uuid"]] = {
                "name": area_dict["name"],
                "spent_total": 0.0,
                "earned": 0.0,
                "penalties": 0.0,
                "penalty_energy": 0.0,
                "total": 0.0,
            }

        if area_dict["type"] == "Area":
            all_child_results = [self.cumulative_bills_results[c["uuid"]]
                                 for c in area_dict["children"]]
            self.cumulative_bills_results[area_dict["uuid"]] = {
                "name": area_dict["name"],
                "spent_total": sum(c["spent_total"] for c in all_child_results),
                "earned": sum(c["earned"] for c in all_child_results),
                "penalties": sum(c["penalties"] for c in all_child_results
                                 if c["penalties"] is not None),
                "penalty_energy": sum(c["penalty_energy"] for c in all_child_results
                                      if c["penalty_energy"] is not None),
                "total": sum(c["total"] for c in all_child_results),
            }
        else:
            parent_area_stats = core_stats.get(area_dict["parent_uuid"], {})
            trades = parent_area_stats.get("trades", [])

            spent_total = sum(trade["price"]
                              for trade in trades
                              if trade["buyer"] == area_dict["name"]) / 100.0
            earned = sum(trade["price"] - trade["fee_price"]
                         for trade in trades
                         if trade["seller"] == area_dict["name"]) / 100.0
            penalty_energy = self._calculate_device_penalties(
                area_dict, core_stats.get(area_dict["uuid"], {})
            )

            if is_load_node_type(area_dict):
                penalty_cost = (
                        penalty_energy * ConstSettings.LoadSettings.LOAD_PENALTY_RATE / 100.0)
            elif is_pv_node_type(area_dict):
                penalty_cost = (
                        penalty_energy * ConstSettings.PVSettings.PV_PENALTY_RATE / 100.0)
            else:
                penalty_cost = 0.0

            total = spent_total - earned + penalty_cost
            self.cumulative_bills_results[area_dict["uuid"]]["spent_total"] += spent_total
            self.cumulative_bills_results[area_dict["uuid"]]["earned"] += earned
            self.cumulative_bills_results[area_dict["uuid"]]["penalties"] += penalty_cost
            self.cumulative_bills_results[area_dict["uuid"]]["penalty_energy"] += penalty_energy
            self.cumulative_bills_results[area_dict["uuid"]]["total"] += total

    # pylint: disable=arguments-differ
    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        raise NotImplementedError(
            "Cumulative bills endpoint supports only global results, merge not supported.")

    @property
    def raw_results(self):
        return self.cumulative_bills

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([self.cumulative_bills_results])


class MarketEnergyBills(ResultsBaseClass):
    """Class to compute the energy bills of a market."""

    def __init__(self, should_export_plots=False):
        self._should_export_plots = should_export_plots
        self.current_raw_bills = {}
        self.bills_results = {}
        self.bills_redis_results = {}
        self.market_fees = {}
        self._cumulative_fee_all_markets_whole_sim = 0.
        self.external_trades = {}

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([
            self.current_raw_bills, self.bills_results, self.bills_redis_results,
            self.market_fees, self.external_trades
        ])

    @staticmethod
    def _store_bought_trade(result_dict, trade):
        trade_price = trade["price"] / 100.
        # Division by 100 to convert cents to Euros
        fee_price = trade["fee_price"] / 100. if trade["fee_price"] is not None else 0.
        result_dict["bought"] += trade["energy"]
        result_dict["spent"] += trade_price - fee_price
        result_dict["total_cost"] += trade_price
        result_dict["total_energy"] += trade["energy"]
        result_dict["market_fee"] += fee_price

    @staticmethod
    def _store_sold_trade(result_dict, trade):
        # Division by 100 to convert cents to Euros
        fee_price = trade["fee_price"] / 100. if trade["fee_price"] is not None else 0.
        result_dict["sold"] += trade["energy"]
        result_dict["total_energy"] -= trade["energy"]
        trade_price = trade["price"] / 100. - fee_price
        result_dict["earned"] += trade_price
        result_dict["total_cost"] -= trade_price

    def _store_outgoing_external_trade(self, trade, area_dict):
        fee_price = trade["fee_price"] if trade["fee_price"] is not None else 0.
        self.external_trades[area_dict["uuid"]]["sold"] += trade["energy"]
        self.external_trades[area_dict["uuid"]]["earned"] += \
            (trade["price"] - fee_price) / 100.
        self.external_trades[area_dict["uuid"]]["total_cost"] -= \
            (trade["price"] - fee_price) / 100.
        self.external_trades[area_dict["uuid"]]["total_energy"] -= trade["energy"]
        self.external_trades[area_dict["uuid"]]["market_fee"] += fee_price / 100.

    def _store_incoming_external_trade(self, trade, area_dict):
        trade_price = trade["price"] / 100.
        fee_price = trade["fee_price"] / 100. if trade["fee_price"] is not None else 0.
        self.external_trades[area_dict["uuid"]]["bought"] += trade["energy"]
        self.external_trades[area_dict["uuid"]]["spent"] += trade_price - fee_price
        self.external_trades[area_dict["uuid"]]["total_cost"] += trade_price
        self.external_trades[area_dict["uuid"]]["total_energy"] += trade["energy"]

    @classmethod
    def _default_area_dict(cls, area_dict):
        area_type = get_unified_area_type(deepcopy(area_dict))
        return dict(bought=0.0, sold=0.0,
                    spent=0.0, earned=0.0,
                    total_energy=0.0, total_cost=0.0,
                    market_fee=0.0,
                    type=area_type)

    # pylint: disable=fixme
    def _get_child_data(self, area_dict):
        if area_dict["uuid"] not in self.current_raw_bills:
            self.current_raw_bills[area_dict["uuid"]] =  \
                {child["uuid"]: self._default_area_dict(child)
                    for child in area_dict["children"]}
        else:
            # TODO: find a better way to handle this.
            # is only triggered once:
            # when a child is added to an area both triggered by a live event
            if area_dict["children"] and "bought" in self.current_raw_bills[area_dict["uuid"]]:
                self.current_raw_bills[area_dict["uuid"]] = {}
            for child in area_dict["children"]:
                self.current_raw_bills[area_dict["uuid"]][child["uuid"]] = \
                    self._default_area_dict(child) \
                    if child["uuid"] not in self.current_raw_bills[area_dict["uuid"]] else \
                    self.current_raw_bills[area_dict["uuid"]][child["uuid"]]

        return self.current_raw_bills[area_dict["uuid"]]

    def _energy_bills(self, area_dict, area_core_stats):
        """
        Return a bill for each of area's children with total energy bought
        and sold (in kWh) and total money earned and spent (in cents).
        Compute bills recursively for children of children etc.
        """
        if area_dict["children"] == []:
            return None

        if area_dict["uuid"] not in self.external_trades:
            self.external_trades[area_dict["uuid"]] = dict(
                bought=0.0, sold=0.0, spent=0.0, earned=0.0,
                total_energy=0.0, total_cost=0.0, market_fee=0.0
            )

        result = self._get_child_data(area_dict)
        child_name_uuid_map = {c["name"]: c["uuid"] for c in area_dict["children"]}

        for trade in area_core_stats[area_dict["uuid"]]["trades"]:
            buyer = area_name_from_area_or_ma_name(trade["buyer"])
            seller = area_name_from_area_or_ma_name(trade["seller"])
            if buyer in child_name_uuid_map:
                self._store_bought_trade(result[child_name_uuid_map[buyer]], trade)
            if seller in child_name_uuid_map:
                self._store_sold_trade(result[child_name_uuid_map[seller]], trade)
            # Outgoing external trades
            if buyer == area_name_from_area_or_ma_name(area_dict["name"]) \
                    and seller in child_name_uuid_map:
                self._store_outgoing_external_trade(trade, area_dict)
            # Incoming external trades
            if seller == area_name_from_area_or_ma_name(area_dict["name"]) \
                    and buyer in child_name_uuid_map:
                self._store_incoming_external_trade(trade, area_dict)
        for child in area_dict["children"]:
            child_result = self._energy_bills(child, area_core_stats)
            if child_result is not None:
                result[child["uuid"]]["children"] = child_result
        return result

    def _accumulate_market_fees(self, area_dict, area_core_stats):
        if area_dict["uuid"] not in self.market_fees:
            self.market_fees[area_dict["uuid"]] = 0.0
        market_fee_eur = area_core_stats[area_dict["uuid"]]["market_fee"] / 100.0
        self.market_fees[area_dict["uuid"]] += market_fee_eur
        self._cumulative_fee_all_markets_whole_sim += market_fee_eur
        for child in area_dict["children"]:
            self._accumulate_market_fees(child, area_core_stats)

    def _update_market_fees(self, area_dict, area_core_stats):
        self._accumulate_market_fees(area_dict, area_core_stats)

    def update(self, area_dict, area_core_stats, current_market_slot):
        if not self._has_update_parameters(
                area_dict, area_core_stats, current_market_slot):
            return
        # Updates the self.market_fees dict which keeps track of the accumulated market fees for
        # each area. Also calculates the cumulative_fee_all_markets_whole_sim, which
        # is the sum of the grid fees for all markets for the whole simulation duration.
        self._update_market_fees(area_dict, area_core_stats)
        # Generate tree of energy bills, following the area_dict structure. Uses uuids
        bills = self._energy_bills(area_dict, area_core_stats)
        flattened = {}
        # Flatten the energy bill tree.
        # The flattened dict contains only area_uuid -> energy_bills_dict, no children
        # or aggregated data like Totals, External Trades etc.
        self._flatten_energy_bills(bills, flattened)
        # Adds children to the flattened dict by iterating over the area_dict, finding out the
        # children of each area, and copying the children bills under their respective parent. Only
        # 1 level child hierarchy.
        # The same function populates the External Trades, Accumulated Trades, Market Fees and
        # Totals bills for the areas that are not leaves (and have children).
        # The naming format of the areas is still uuid
        bills = self._accumulate_by_children(area_dict, flattened, {})
        # Keep the state of the unformatted bills in order to be reused by _energy_bills method.
        # We need this in order to read past results when calculating the new energy bills.
        self.current_raw_bills = deepcopy(bills)
        # Converts the children of the bills from uuids to names, because the UI uses these
        # as headers in the table where these data are reported.
        bills = self._swap_children_uuids_to_names(area_dict, bills)
        # Converts the keys of the result dict from uuids to names, in order to end up in
        # the CSV files in a human-readable format.
        if self._should_export_plots:
            self.bills_results = self._bills_local_format(area_dict, bills)
        # Rounds the precision of the results to 3 decimal points, in order for the UI to report
        # them correctly.
        self.bills_redis_results = self._round_results_for_ui(deepcopy(bills))

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        self.bills_redis_results[area_dict["uuid"]] = last_known_state_data
        self.bills_results[area_dict["name"]] = last_known_state_data
        self.current_raw_bills[area_dict["uuid"]] = \
            self._swap_children_names_to_uuids(area_dict, area_dict["uuid"], last_known_state_data)

        if "External Trades" in last_known_state_data:
            external = last_known_state_data["External Trades"]
            self.external_trades[area_dict["uuid"]] = {}
            self.external_trades[area_dict["uuid"]].update(
                {"bought": external.get("sold", 0.), "sold": external.get("bought", 0.),
                 "spent": external.get("earned", 0.), "earned": external.get("spent", 0.),
                 "market_fee": external.get("market_fee", 0.)}
            )
            self.external_trades[area_dict["uuid"]]["total_energy"] = \
                self.external_trades[area_dict["uuid"]]["bought"] - \
                self.external_trades[area_dict["uuid"]]["sold"]
            self.external_trades[area_dict["uuid"]]["total_cost"] = \
                self.external_trades[area_dict["uuid"]]["spent"] - \
                self.external_trades[area_dict["uuid"]]["earned"] + \
                self.external_trades[area_dict["uuid"]]["market_fee"]

    def restore_cumulative_fees_whole_sim(self, cumulative_fees):
        """Replace the existing cumulative fees with the fees provided as argument."""
        self._cumulative_fee_all_markets_whole_sim = cumulative_fees

    @classmethod
    def _flatten_energy_bills(cls, energy_bills, flat_results):
        for area_uuid, bills in energy_bills.items():
            if "children" in bills:
                cls._flatten_energy_bills(bills["children"], flat_results)
            flat_results[area_uuid] = copy(bills)
            flat_results[area_uuid].pop("children", None)

    def _accumulate_by_children(self, area_dict, flattened, results):
        if not area_dict["children"]:
            # This is a device
            results[area_dict["uuid"]] = flattened.get(area_dict["uuid"],
                                                       self._default_area_dict(area_dict))
        else:
            results[area_dict["uuid"]] = {
                child["uuid"]: flattened[child["uuid"]]
                for child in area_dict["children"]
                if child["uuid"] in flattened}

            results.update(**self._generate_external_and_total_bills(area_dict, results))

            for child in area_dict["children"]:
                results.update(**self._accumulate_by_children(child, flattened, results))

        return results

    @staticmethod
    def _write_accumulated_stats(area_dict, results, all_child_results, key_name):
        results[area_dict["uuid"]].update({key_name: {
            "bought": sum(v["bought"] for v in all_child_results),
            "sold": sum(v["sold"] for v in all_child_results),
            "spent": sum(v["spent"] for v in all_child_results),
            "earned": sum(v["earned"] for v in all_child_results),
            "total_energy": sum(v["total_energy"] for v in all_child_results),
            "total_cost": sum(v["total_cost"]
                              for v in all_child_results),
            "market_fee": sum(v["market_fee"]
                              for v in all_child_results)
        }})

    @staticmethod
    def _market_fee_section(market_fee):
        return {"Market Fees": {
                    "bought": 0,
                    "sold": 0,
                    "spent": 0,
                    "earned": market_fee,
                    "market_fee": 0,
                    "total_energy": 0,
                    "total_cost": -1 * market_fee
                    }}

    def _generate_external_and_total_bills(self, area_dict, results):
        all_child_results = list(results[area_dict["uuid"]].values())
        self._write_accumulated_stats(area_dict, results, all_child_results, "Accumulated Trades")
        total_market_fee = results[area_dict["uuid"]]["Accumulated Trades"]["market_fee"]
        if area_dict["uuid"] in self.external_trades:
            # External trades are the trades of the parent area
            external = self.external_trades[area_dict["uuid"]].copy()
            # Should switch spent/earned and bought/sold, to match the perspective of the UI
            spent = external.pop("spent")
            earned = external.pop("earned")
            bought = external.pop("bought")
            sold = external.pop("sold")
            total_external_fee = external.pop("market_fee")
            external.update(**{
                "spent": earned, "earned": spent, "bought": sold,
                "sold": bought, "market_fee": total_external_fee})
            external["total_energy"] = external["bought"] - external["sold"]
            external["total_cost"] = external["spent"] - external["earned"] + total_external_fee
            results[area_dict["uuid"]].update({"External Trades": external})

            total_market_fee += total_external_fee
            results[area_dict["uuid"]].update(self._market_fee_section(total_market_fee))
            totals_child_list = [results[area_dict["uuid"]]["Accumulated Trades"],
                                 results[area_dict["uuid"]]["External Trades"],
                                 results[area_dict["uuid"]]["Market Fees"]]
        else:
            # If root area, Accumulated Trades == Totals
            results[area_dict["uuid"]].update(self._market_fee_section(total_market_fee))
            totals_child_list = [results[area_dict["uuid"]]["Accumulated Trades"],
                                 results[area_dict["uuid"]]["Market Fees"]]

        self._write_accumulated_stats(area_dict, results, totals_child_list, "Totals")
        return results

    @classmethod
    def _bills_local_format(cls, area_dict, bills_results_uuids):
        bills_results = {}
        if area_dict["uuid"] in bills_results_uuids:
            bills_results[area_dict["name"]] = bills_results_uuids[area_dict["uuid"]]
        for child in area_dict["children"]:
            if child["children"]:
                bills_results.update(cls._bills_local_format(child, bills_results_uuids))
            elif child["uuid"] in bills_results_uuids:
                bills_results[child["name"]] = bills_results_uuids[child["uuid"]]
        return bills_results

    @classmethod
    def _swap_children_uuids_to_names(cls, area_dict, bills_results):
        area_uuid_name_mapping = get_area_uuid_name_mapping(area_dict, {})
        final_result = {}
        for k, children in bills_results.items():
            children_result = {}
            if "bought" in children:
                final_result[k] = children
                continue
            for uuid, child in children.items():
                if uuid in ["Totals", "Accumulated Trades", "External Trades", "Market Fees"] or \
                        uuid not in area_uuid_name_mapping:
                    children_result[uuid] = child
                else:
                    children_result[area_uuid_name_mapping[uuid]] = child

            final_result[k] = children_result
        return final_result

    @classmethod
    def _swap_children_names_to_uuids(cls, area_dict, area_uuid, area_results):
        if not key_in_dict_and_not_none(area_dict, "children"):
            return {}

        if key_in_dict_and_not_none(area_dict, "name") and \
                key_in_dict_and_not_none(area_dict, "uuid") and \
                area_uuid == area_dict["uuid"]:
            child_name_uuid_mapping = {c["name"]: c["uuid"] for c in area_dict["children"]}
            return {
                child_name_uuid_mapping.get(k, k): v for k, v in area_results.items()
            }

        for child in area_dict["children"]:
            converted_result = cls._swap_children_names_to_uuids(child, area_uuid, area_results)
            if converted_result:
                return converted_result
        return {}

    @classmethod
    def _round_child_bill_results(cls, results):
        results["bought"] = round_floats_for_ui(results["bought"])
        results["sold"] = round_floats_for_ui(results["sold"])
        results["spent"] = round_floats_for_ui(results["spent"])
        results["earned"] = round_floats_for_ui(results["earned"])
        results["total_energy"] = round_floats_for_ui(results["total_energy"])
        results["total_cost"] = round_floats_for_ui(results["total_cost"])
        if "market_fee" in results:
            results["market_fee"] = round_floats_for_ui(results["market_fee"])
        return results

    @classmethod
    def _round_results_for_ui(cls, results):
        rounded_results = {}
        for uuid, area_results in results.items():
            if "bought" in area_results:
                rounded_results[uuid] = cls._round_child_bill_results(area_results)
            else:
                rounded_results[uuid] = {
                    c_name: cls._round_child_bill_results(child_results)
                    for c_name, child_results in area_results.items()
                }
        return rounded_results

    # pylint: disable=arguments-differ
    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        raise NotImplementedError(
            "Bills endpoint supports only global results, merge not supported.")

    @property
    def raw_results(self):
        return self.bills_results

    @property
    def ui_formatted_results(self):
        return self.bills_redis_results

    @property
    def cumulative_fee_all_markets_whole_sim(self):
        """Return the cumulative fee of all markets in the entire simulation."""
        return self._cumulative_fee_all_markets_whole_sim
