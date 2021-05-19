import logging
from time import time

from typing import Dict

from d3a_interface.sim_results.area_throughput_stats import AreaThroughputStats
from d3a_interface.sim_results.bills import MarketEnergyBills, CumulativeBills
from d3a_interface.sim_results.cumulative_grid_trades import CumulativeGridTrades
from d3a_interface.sim_results.cumulative_net_energy_flow import CumulativeNetEnergyFlow
from d3a_interface.sim_results.device_statistics import DeviceStatistics
from d3a_interface.sim_results.energy_trade_profile import EnergyTradeProfile
from d3a_interface.sim_results.kpi import KPI
from d3a_interface.sim_results.market_price_energy_day import MarketPriceEnergyDay
from d3a_interface.sim_results.market_summary_info import MarketSummaryInfo
from d3a_interface.sim_results.simulation_assets_info import SimulationAssetsInfo


class ResultsHandler:
    def __init__(self, should_export_plots: bool = False):
        self.should_export_plots = should_export_plots
        self.bids_offers_trades = {}
        self.results_mapping = {
            'bills': MarketEnergyBills(should_export_plots),
            'kpi': KPI(),
            'cumulative_net_energy_flow': CumulativeNetEnergyFlow(),
            'price_energy_day': MarketPriceEnergyDay(should_export_plots),
            'cumulative_bills': CumulativeBills(),
            'cumulative_grid_trades': CumulativeGridTrades(),
            'device_statistics': DeviceStatistics(should_export_plots),
            'trade_profile': EnergyTradeProfile(should_export_plots),
            'area_throughput': AreaThroughputStats(),
            'market_summary': MarketSummaryInfo(should_export_plots),
            'assets_info': SimulationAssetsInfo()
        }
        self._total_memory_utilization_kb = 0.0

    @property
    def _results_name_to_db_name_mapping(self):
        mapping = {
            k: k for k in self.results_mapping.keys()
        }
        mapping.update({
            "bills": "price_energy_area_balance",
            "trade_profile": "energy_trade_profile",
            "area_throughput_stats": "area_throughput",
        })
        return mapping

    def _update_memory_utilization(self):
        t1 = time()
        self._total_memory_utilization_kb = sum([
            v.memory_allocation_size_kb()
            for k, v in self.results_mapping.items()
        ])
        t2 = time()
        logging.info(f"Memory allocation calculation lasted {t2 -t1}. "
                     f"Total allocated memory {self._total_memory_utilization_kb}")

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str):
        for area_uuid, area_result in core_stats.items():
            self.bids_offers_trades[area_uuid] = \
                {k: area_result.get(k, []) for k in ('offers', 'bids', 'trades')}
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
        if cumulative_grid_fees is not None:
            self.results_mapping["bills"].restore_cumulative_fees_whole_sim(cumulative_grid_fees)
        if assets_info is not None:
            self.results_mapping["assets_info"].restore_assets_info(assets_info)
        if area_results_map.get(config_tree['uuid'], {}):
            area_results = area_results_map[config_tree['uuid']]
            for k, v in self.results_mapping.items():
                db_field_name = self._results_name_to_db_name_mapping[k]
                if db_field_name not in area_results:
                    continue
                else:
                    self.results_mapping[k].restore_area_results_state(
                        config_tree, area_results[db_field_name]
                    )

        for child in config_tree['children']:
            self.restore_area_results_state(child, area_results_map)

    @property
    def all_raw_results(self) -> Dict:
        return {
            k: v.raw_results
            for k, v in self.results_mapping.items()
        }

    @property
    def all_ui_results(self) -> Dict:
        return {
            k: v.ui_formatted_results
            for k, v in self.results_mapping.items()
        }

    @property
    def all_db_results(self) -> Dict:
        results = {
            self._results_name_to_db_name_mapping[k]: v.ui_formatted_results
            for k, v in self.results_mapping.items()
        }
        results["bids_offers_trades"] = self.bids_offers_trades
        results["cumulative_market_fees"] = \
            self.results_mapping["bills"].cumulative_fee_all_markets_whole_sim
        return results

    @property
    def trade_profile_plot_results(self):
        return self.results_mapping["trade_profile"].plot_results

    @property
    def total_memory_utilization_kb(self):
        return self._total_memory_utilization_kb
