import logging
import traceback
from time import time
from typing import Dict

from gsy_framework.sim_results.area_throughput_stats import AreaThroughputStats
from gsy_framework.sim_results.bills import CumulativeBills, MarketEnergyBills
from gsy_framework.sim_results.cumulative_grid_trades import CumulativeGridTrades
from gsy_framework.sim_results.cumulative_net_energy_flow import CumulativeNetEnergyFlow
from gsy_framework.sim_results.device_statistics import DeviceStatistics
from gsy_framework.sim_results.energy_trade_profile import EnergyTradeProfile
from gsy_framework.sim_results.kpi import KPI
from gsy_framework.sim_results.market_price_energy_day import MarketPriceEnergyDay
from gsy_framework.sim_results.market_summary_info import MarketSummaryInfo
from gsy_framework.sim_results.scm.bills import SCMBills
from gsy_framework.sim_results.scm.kpi import SCMKPI
from gsy_framework.sim_results.simulation_assets_info import SimulationAssetsInfo
from gsy_framework.sim_results.imported_exported_energy import ImportedExportedEnergyHandler


class ResultsHandler:
    """Calculate all results for each market slot."""

    def __init__(self, should_export_plots: bool = False):
        self.forward_market_enabled = False
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
            "assets_info": SimulationAssetsInfo(),
            "imported_exported_energy": ImportedExportedEnergyHandler(should_export_plots),
            "bills": MarketEnergyBills(should_export_plots),
            "market_summary": MarketSummaryInfo(should_export_plots),
        }

        self._total_memory_utilization_kb = 0.0

    def _update_memory_utilization(self):
        start_time = time()
        self._total_memory_utilization_kb = sum(
            [v.memory_allocation_size_kb() for k, v in self.results_mapping.items()]
        )
        end_time = time()
        logging.info(
            "Memory allocation calculation lasted %s. Total allocated memory %s",
            end_time - start_time,
            self._total_memory_utilization_kb,
        )

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str):
        """Update all simulation results. Should be called after every market cycle."""
        for area_uuid, area_result in core_stats.items():
            self.bids_offers_trades[area_uuid] = {
                k: area_result.get(k, []) for k in ("offers", "bids", "trades")
            }
        for result_object in self.results_mapping.values():
            try:
                result_object.update(area_dict, core_stats, current_market_slot)
            except Exception as ex:  # pylint: disable=broad-except
                logging.error(
                    "Result calculation failed on market slot %s with error %s, %s",
                    current_market_slot,
                    str(ex),
                    traceback.format_exc(),
                )

        self._update_memory_utilization()

    def update_from_repr(self, area_representation: Dict):
        """
        Can be added as an abstract method to the results_abc if needed
        """
        for result_object in self.results_mapping.values():
            result_object.update_from_repr(area_representation)

    def restore_area_results_state(
        self, config_tree, area_results_map, cumulative_grid_fees=None, assets_info=None
    ):
        """Restore all area results from the state persisted to the DB."""
        if cumulative_grid_fees is not None:
            self.results_mapping["bills"].restore_cumulative_fees_whole_sim(cumulative_grid_fees)
        if assets_info is not None:
            self.results_mapping["assets_info"].restore_assets_info(assets_info)
        if area_results_map.get(config_tree["uuid"], {}):
            area_results = area_results_map[config_tree["uuid"]]
            for db_field_name, result_object in self.results_mapping.items():
                if db_field_name not in area_results:
                    continue
                result_object.restore_area_results_state(config_tree, area_results[db_field_name])

        for child in config_tree["children"]:
            self.restore_area_results_state(child, area_results_map)

    @property
    def all_raw_results(self) -> Dict:
        """Get all results in raw format."""
        return {k: v.raw_results for k, v in self.results_mapping.items()}

    @property
    def all_ui_results(self) -> Dict:
        """Get all results in format to be consumed by the UI."""
        return {k: v.ui_formatted_results for k, v in self.results_mapping.items()}

    @property
    def all_db_results(self) -> Dict:
        """Get dict with all the results in format that can be saved to the DB."""
        results = {k: v.ui_formatted_results for k, v in self.results_mapping.items()}
        results["bids_offers_trades"] = self.bids_offers_trades
        results["cumulative_market_fees"] = self.results_mapping[
            "bills"
        ].cumulative_fee_all_markets_whole_sim
        return results

    @property
    def trade_profile_plot_results(self):
        """Get plot results for the trade profile."""
        return self.results_mapping["trade_profile"].plot_results

    @property
    def total_memory_utilization_kb(self):
        """Get the total memory allocated by the results."""
        return self._total_memory_utilization_kb


class SCMResultsHandler(ResultsHandler):
    """Calculate all results for each market slot for SCM simulations"""

    def __init__(self):
        super().__init__()
        self.results_mapping = {
            "cumulative_net_energy_flow": CumulativeNetEnergyFlow(),
            "bills": SCMBills(),
            "kpi": SCMKPI(),
        }

    @property
    def all_db_results(self) -> Dict:
        """Get dict with all the results in format that can be saved to the DB."""
        results = {
            self._results_name_to_db_name_mapping[k]: v.ui_formatted_results
            for k, v in self.results_mapping.items()
        }
        results["bids_offers_trades"] = self.bids_offers_trades
        results["cumulative_market_fees"] = 0.0
        return results
