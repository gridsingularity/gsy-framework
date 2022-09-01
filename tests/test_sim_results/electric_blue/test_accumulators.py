from pendulum import DateTime, duration

from gsy_framework.sim_results.aggregate_results import MarketResultsAggregator
from gsy_framework.sim_results.electric_blue.accumulators import \
    EBEnergyTradeProfileAccumulator
from tests.test_sim_results.test_aggregate_results import (
    MARKET_TIMESLOTS, ORDERS_PER_MARKET_SLOT, gen_market_stats)


class TestEBAccumulators:
    @staticmethod
    def test_energy_traded_profile():
        """Test energy traded profile is accumulated correctly through different timeslots."""
        resolution = duration(minutes=30)
        simulation_slot_length = duration(minutes=15)
        simulation_start_time = DateTime(2020, 1, 1, 0, 0)
        mra = MarketResultsAggregator(
            resolution=resolution,
            simulation_slot_length=simulation_slot_length,
            accumulators={"energy_traded_profile": EBEnergyTradeProfileAccumulator()}
        )
        market_stats_gen = gen_market_stats(
            start_time=simulation_start_time,
            slot_length=simulation_slot_length)

        for _ in range(2):
            mra.update(*next(market_stats_gen))

        aggregated_results = list(mra.generate())[0]
        assert aggregated_results["accumulated_results"]["energy_traded_profile"]["SELLER"] == {
            "total_buy_trade_count": 0,
            "total_earned_eur": 30 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 2,
            "total_energy_bought": 0,
            "total_energy_consumed": 0,
            "total_energy_produced": 0,
            "total_energy_sold": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 2,
            "total_sell_trade_count": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 2,
            "total_spent_eur": 0
        }
        assert aggregated_results["accumulated_results"]["energy_traded_profile"]["BUYER"] == {
            "total_buy_trade_count": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 2,
            "total_earned_eur": 0,
            "total_energy_bought": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 2,
            "total_energy_consumed": 0,
            "total_energy_produced": 0,
            "total_energy_sold": 0,
            "total_sell_trade_count": 0,
            "total_spent_eur": 30 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 2
        }

        for _ in range(10):
            mra.update(*next(market_stats_gen))

        aggregated_results = list(mra.generate())[-1]
        assert aggregated_results["accumulated_results"]["energy_traded_profile"]["SELLER"] == {
            "total_buy_trade_count": 0,
            "total_earned_eur": 30 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 12,
            "total_energy_bought": 0,
            "total_energy_consumed": 0,
            "total_energy_produced": 0,
            "total_energy_sold": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 12,
            "total_sell_trade_count": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 12,
            "total_spent_eur": 0
        }
        assert aggregated_results["accumulated_results"]["energy_traded_profile"]["BUYER"] == {
            "total_buy_trade_count": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 12,
            "total_earned_eur": 0,
            "total_energy_bought": 1 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 12,
            "total_energy_consumed": 0,
            "total_energy_produced": 0,
            "total_energy_sold": 0,
            "total_sell_trade_count": 0,
            "total_spent_eur": 30 * ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS * 12
        }
