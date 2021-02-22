from typing import Dict
from d3a_interface.sim_results.market_price_energy_day import MarketPriceEnergyDay
from d3a_interface.sim_results.area_throughput_stats import AreaThroughputStats
from d3a_interface.sim_results.bills import MarketEnergyBills, CumulativeBills
from d3a_interface.sim_results.device_statistics import DeviceStatistics
from d3a_interface.sim_results.export_unmatched_loads import MarketUnmatchedLoads
from d3a_interface.sim_results.energy_trade_profile import EnergyTradeProfile
from d3a_interface.sim_results.cumulative_grid_trades import CumulativeGridTrades
from d3a_interface.sim_results.kpi import KPI


class ResultsHandler:
    def __init__(self, should_export_plots: bool = True):
        self.should_export_plots = should_export_plots
        if self.should_export_plots:
            self.results_mapping = {
                "bills": MarketEnergyBills(should_export_plots),
                "kpi": KPI(),
                "unmatched_loads": MarketUnmatchedLoads(),
                "price_energy_day": MarketPriceEnergyDay(should_export_plots),
                "cumulative_bills": CumulativeBills(),
                "cumulative_grid_trades": CumulativeGridTrades(),
                "device_statistics": DeviceStatistics(should_export_plots),
                "trade_profile": EnergyTradeProfile(should_export_plots),
                "area_throughput_stats": AreaThroughputStats(),
            }
        else:
            self.results_mapping = {
                "bills": MarketEnergyBills(should_export_plots),
                "kpi": KPI()
            }

    def update(self, area_dict: Dict, core_stats: Dict, current_market_slot: str):
        for _, v in self.results_mapping.items():
            v.update(area_dict, core_stats, current_market_slot)

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
    def trade_profile_plot_results(self):
        return self.results_mapping["trade_profile"].plot_results
