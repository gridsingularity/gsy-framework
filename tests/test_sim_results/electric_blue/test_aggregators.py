from pendulum import DateTime, duration

from gsy_framework.sim_results.aggregate_results import MarketResultsAggregator
from gsy_framework.sim_results.electric_blue.aggregators import \
    EBEnergyProfileAggregator
from tests.test_sim_results.test_aggregate_results import gen_market_stats


class TestEBAggregator:
    @staticmethod
    def test_energy_profile():
        """Test energy traded profile is aggregated correctly
        for each time period (resolution)."""
        resolution = duration(minutes=30)
        simulation_slot_length = duration(minutes=15)
        simulation_start_time = DateTime(2020, 1, 1, 0, 0)
        mra = MarketResultsAggregator(
            resolution=resolution,
            simulation_slot_length=simulation_slot_length,
            aggregators={"energy_profile": EBEnergyProfileAggregator()}
        )
        market_stats_gen = gen_market_stats(
            start_time=simulation_start_time,
            slot_length=simulation_slot_length)

        for _ in range(2):
            mra.update(*next(market_stats_gen))

        aggregated_results = list(mra.generate())[0]
        aggregated_results = aggregated_results["aggregated_results"]["energy_profile"]
        assert aggregated_results["SELLER"] == {
            "open_buy_orders": 0.0,
            "open_sell_orders": 200.0,
            "matched_buy_orders": 0.0,
            "matched_sell_orders": 40.0,
            "all_buy_orders": 0.0,
            "all_sell_orders": 240.0
        }
        assert aggregated_results["BUYER"] == {
            "open_buy_orders": 200.0,
            "open_sell_orders": 0.0,
            "matched_buy_orders": 40.0,
            "matched_sell_orders": 0.0,
            "all_buy_orders": 240.0,
            "all_sell_orders": 0.0
        }
