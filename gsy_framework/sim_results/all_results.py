from collections import defaultdict
import logging
from time import time
from typing import Dict

from gsy_framework.constants_limits import GlobalConfig
from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.sim_results.aggregate_results import (AggregationTimeManager,
                                                         MarketResultsAggregator,
                                                         MARKET_RESOLUTIONS,
                                                         RESOLUTION_AGGREGATIONS)
from gsy_framework.sim_results.area_throughput_stats import AreaThroughputStats
from gsy_framework.sim_results.bills import CumulativeBills, MarketEnergyBills
from gsy_framework.sim_results.cumulative_grid_trades import \
    CumulativeGridTrades
from gsy_framework.sim_results.cumulative_net_energy_flow import \
    CumulativeNetEnergyFlow
from gsy_framework.sim_results.device_statistics import DeviceStatistics
from gsy_framework.sim_results.energy_trade_profile import EnergyTradeProfile
from gsy_framework.sim_results.kpi import KPI
from gsy_framework.sim_results.market_price_energy_day import \
    MarketPriceEnergyDay
from gsy_framework.sim_results.market_summary_info import MarketSummaryInfo
from gsy_framework.sim_results.scm.kpi import SCMKPI
from gsy_framework.sim_results.simulation_assets_info import \
    SimulationAssetsInfo
from pendulum import duration, DateTime


class ForwardResultsHandler:
    """Calculate all results for each market slot for forward markets."""

    def __init__(self, simulation_start_time: DateTime):
        self.forward_market_enabled = True
        self.results_aggregator: Dict[str, Dict[str, MarketResultsAggregator]] = defaultdict(dict)
        self.aggregated_data: Dict[str, Dict[str, Dict]] = defaultdict(dict)
        self.bids_offers_trades: Dict[str, Dict[str, Dict]] = defaultdict(dict)
        self.aggregation_time_manager = AggregationTimeManager(simulation_start_time)
        self._total_memory_utilization_kb = 0.0

    def _update_memory_utilization(self) -> None:
        pass

    def _create_market_results_aggregators(self, area_uuid: str) -> None:
        """Create results aggregators for specific forward market types and their resolutions."""
        for market_type, resolutions in MARKET_RESOLUTIONS.items():
            for resolution in resolutions:
                market_type_value = str(market_type.value)
                self.results_aggregator[area_uuid][market_type_value] = MarketResultsAggregator(
                    resolution=resolution.duration(),
                    simulation_slot_length=duration(minutes=GlobalConfig.SLOT_LENGTH_M),
                    aggregators=RESOLUTION_AGGREGATIONS.get(resolution, {}).get(
                        "aggregators", {}),
                    accumulators=RESOLUTION_AGGREGATIONS.get(resolution, {}).get(
                        "accumulators", {}))

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str) -> None:
        """Update the forward market aggregated results with bids_offers_trades of current slot.
        forward_market_results_aggregator= {'240f6c9a-addd-427f-892b-e1ebe298c551': {'8': {
            '2020-01-01T00:00:00': {'bids': [...], 'offers': [...], 'trades': [...]},
        """
        for area_uuid, area_result in core_stats.items():
            if "forward_market_stats" not in area_result:
                return

            if area_uuid not in self.results_aggregator:
                self._create_market_results_aggregators(area_uuid)

            for market_type_value, market_stats in area_result["forward_market_stats"].items():

                self.bids_offers_trades[area_uuid][market_type_value] = market_stats

                market_type = AvailableMarketTypes(int(market_type_value))
                if market_type_value in [str(market.value) for market in MARKET_RESOLUTIONS]:
                    results_aggregator = self.results_aggregator[area_uuid][market_type_value]

                    results_aggregator.update(current_market_slot, market_stats)

                    current_market_slot_dt = DateTime.fromisoformat(current_market_slot)
                    for resolution in MARKET_RESOLUTIONS.get(market_type):
                        aggregation_windows = \
                            self.aggregation_time_manager.get_aggregation_windows(
                                current_market_slot_dt,
                                resolution.duration(),
                                results_aggregator.last_aggregation_time)
                        if aggregation_windows:
                            aggregated_results = list(results_aggregator.generate())
                            if aggregated_results:
                                self.aggregated_data[area_uuid][market_type_value] = \
                                    aggregated_results[0]

        self._update_memory_utilization()

    def update_from_repr(self, area_representation: Dict):
        """
        Updates the simulation results using area_representation data that arrive from the d3a-web
        """
        pass

    @property
    def all_db_results(self) -> Dict:
        """Get dict with all the results in format that can be saved to the DB."""
        results = {"bids_offers_trades": self.bids_offers_trades}
        if self.aggregated_data:
            results["aggregated_results"] = self.aggregated_data
            self.aggregated_data = {}
        results["cumulative_net_energy_flow"] = {}
        results["cumulative_market_fees"] = 0.

        return results

    @property
    def total_memory_utilization_kb(self):
        """Get the total memory allocated by the results."""
        return self._total_memory_utilization_kb


class ResultsHandler:
    """Calculate all results for each market slot."""

    def __init__(self, should_export_plots: bool = False, is_scm: bool = False):
        self.forward_market_enabled = False
        self._is_scm = is_scm
        self.should_export_plots = should_export_plots
        self.bids_offers_trades = {}
        self.results_mapping = {
            "kpi": KPI(),
            "cumulative_net_energy_flow": CumulativeNetEnergyFlow(),
            "price_energy_day": MarketPriceEnergyDay(should_export_plots),
            "cumulative_bills": CumulativeBills(),
            "cumulative_grid_trades": CumulativeGridTrades(),
            "device_statistics": DeviceStatistics(should_export_plots),
            "trade_profile": EnergyTradeProfile(should_export_plots),
            "area_throughput": AreaThroughputStats(),
            "assets_info": SimulationAssetsInfo()
        }

        if is_scm:
            self.results_mapping["bills"] = MarketEnergyBills(should_export_plots)
            self.results_mapping["kpi"] = SCMKPI()
        else:
            self.results_mapping["bills"] = MarketEnergyBills(should_export_plots)
            self.results_mapping["market_summary"] = MarketSummaryInfo(should_export_plots)

        self._total_memory_utilization_kb = 0.0

    @property
    def _results_name_to_db_name_mapping(self):
        mapping = {
            k: k for k in self.results_mapping
        }
        mapping.update({
            "bills": "price_energy_area_balance",
            "trade_profile": "energy_trade_profile",
            "area_throughput_stats": "area_throughput",
        })
        return mapping

    def _update_memory_utilization(self):
        start_time = time()
        self._total_memory_utilization_kb = sum([
            v.memory_allocation_size_kb()
            for k, v in self.results_mapping.items()
        ])
        end_time = time()
        logging.info("Memory allocation calculation lasted %s. Total allocated memory %s",
                     end_time - start_time, self._total_memory_utilization_kb)

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str):
        """Update all simulation results. Should be called after every market cycle."""
        for area_uuid, area_result in core_stats.items():
            self.bids_offers_trades[area_uuid] = \
                {k: area_result.get(k, []) for k in ("offers", "bids", "trades")}
        for result_object in self.results_mapping.values():
            result_object.update(area_dict, core_stats, current_market_slot)
        self._update_memory_utilization()

    def update_from_repr(self, area_representation: Dict):
        """
        Can be added as an abstract method to the results_abc if needed
        """
        for result_object in self.results_mapping.values():
            result_object.update_from_repr(area_representation)

    def restore_area_results_state(self, config_tree, area_results_map,
                                   cumulative_grid_fees=None, assets_info=None):
        """Restore all area results from the state persisted to the DB."""
        if cumulative_grid_fees is not None:
            self.results_mapping["bills"].restore_cumulative_fees_whole_sim(cumulative_grid_fees)
        if assets_info is not None:
            self.results_mapping["assets_info"].restore_assets_info(assets_info)
        if area_results_map.get(config_tree["uuid"], {}):
            area_results = area_results_map[config_tree["uuid"]]
            for k, result_object in self.results_mapping.items():
                db_field_name = self._results_name_to_db_name_mapping[k]
                if db_field_name not in area_results:
                    continue
                result_object.restore_area_results_state(
                    config_tree, area_results[db_field_name]
                )

        for child in config_tree["children"]:
            self.restore_area_results_state(child, area_results_map)

    @property
    def all_raw_results(self) -> Dict:
        """Get all results in raw format."""
        return {
            k: v.raw_results
            for k, v in self.results_mapping.items()
        }

    @property
    def all_ui_results(self) -> Dict:
        """Get all results in format to be consumed by the UI."""
        return {
            k: v.ui_formatted_results
            for k, v in self.results_mapping.items()
        }

    @property
    def all_db_results(self) -> Dict:
        """Get dict with all the results in format that can be saved to the DB."""
        results = {
            self._results_name_to_db_name_mapping[k]: v.ui_formatted_results
            for k, v in self.results_mapping.items()
        }
        results["bids_offers_trades"] = self.bids_offers_trades
        if not self._is_scm:
            results["cumulative_market_fees"] = \
                self.results_mapping["bills"].cumulative_fee_all_markets_whole_sim
        else:
            results["cumulative_market_fees"] = 0.
        return results

    @property
    def trade_profile_plot_results(self):
        """Get plot results for the trade profile."""
        return self.results_mapping["trade_profile"].plot_results

    @property
    def total_memory_utilization_kb(self):
        """Get the total memory allocated by the results."""
        return self._total_memory_utilization_kb
