from random import shuffle
from unittest.mock import MagicMock

import pytest
from pendulum import DateTime, Duration, duration

from gsy_framework.sim_results.aggregate_results import MarketResultsAggregator

DEFAULT_SIMULATION_SLOT_LENGTH = duration(minutes=15)
MARKET_TIMESLOTS = 10
ORDERS_PER_MARKET_SLOT = 2


class TestMarketResultsAggregator:

    @staticmethod
    def gen_market_stats(start_time: DateTime, slot_length: Duration):
        """Simulate market stats{bids,offers,trades} for each timeslot."""
        while True:
            market_stats = {}
            market_timeslot = start_time
            for _ in range(MARKET_TIMESLOTS):
                market_stats[str(market_timeslot)] = {
                    "bids": [MagicMock(
                        creation_time=start_time, timeslot=market_timeslot)
                        for _ in range(ORDERS_PER_MARKET_SLOT)],
                    "offers": [MagicMock(
                        creation_time=start_time, timeslot=market_timeslot)
                        for _ in range(ORDERS_PER_MARKET_SLOT)],
                    "trades": [MagicMock(
                        creation_time=start_time, timeslot=market_timeslot)
                        for _ in range(ORDERS_PER_MARKET_SLOT)]
                }
                market_timeslot += slot_length
            yield start_time, market_stats
            start_time += slot_length

    def test_bids_offers_trades_buffer_gets_updated(self):
        """Test if bids_offers_trades buffer of the MarketResultsAggregator gets
        updated on each call to its update()/generate() method.
        Also, check that the correct number of bids/offers/trades are stored at each timeslot.
        """
        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        market_stats_gen = self.gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=Duration(minutes=15))

        added_timeslots = []

        for _ in range(4):
            current_timeslot, market_stat = next(market_stats_gen)
            market_results_aggr.update(current_timeslot, market_stat)
            added_timeslots.append(current_timeslot)

            for order in ("bids", "offers", "trades"):
                # check correct number of orders are saved per timeslot
                assert len(set(market_results_aggr.bids_offers_trades[current_timeslot][order])
                           ) == ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS

            # check all the added timeslots are still there.
            assert all(timeslot in market_results_aggr.bids_offers_trades for
                       timeslot in added_timeslots)
            # check no extra timeslot is saved.
            assert len(market_results_aggr.bids_offers_trades) == len(added_timeslots)

        # check no duplicated entries are added for each timeslot
        for order in ("bids", "offers", "trades"):
            buffered_orders = set()
            for market_stats in market_results_aggr.bids_offers_trades.values():
                buffered_orders = buffered_orders.union(set(market_stats[order]))
            assert len(buffered_orders) == 4 * MARKET_TIMESLOTS * ORDERS_PER_MARKET_SLOT

        # only one result should be generated for slot_length=15m and resolution=1h.
        assert len(list(market_results_aggr.generate())) == 1
        # data should be cleared from cache once it's processed.
        assert len(market_results_aggr.bids_offers_trades) == 0

    def test_correct_timeslots_are_being_consumed(self):
        """Test that correct consequent timeslots are being consumed and
        others remain unused in the buffer. Also, make sure that the
        order of updates doesn't affect the final result."""

        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        simulation_start_time = DateTime(2020, 1, 1, 0, 0)
        market_stats_gen = self.gen_market_stats(
            simulation_start_time, slot_length=Duration(minutes=15))

        # collect market stats for 5 slots and reorder them
        market_stats = [next(market_stats_gen) for _ in range(5)]
        shuffle(market_stats)

        for current_timeslot, market_stat in market_stats:
            market_results_aggr.update(current_timeslot, market_stat)

        aggregated_result = list(market_results_aggr.generate())
        assert len(aggregated_result) == 1
        assert aggregated_result[0]["start_time"] == simulation_start_time

        # As the resolution is 1 hour, and each timeslot is 15 minutes,
        # the market_results_aggr should consume 4 data points per each aggregation.
        # This means that the last data point should be remained in the buffer.
        assert len(market_results_aggr.bids_offers_trades) == 1
        next_time = list(market_results_aggr.bids_offers_trades.keys())[0]

        # given 3 more slots data, it should generate the next aggregated result
        market_stats = [next(market_stats_gen) for _ in range(3)]
        shuffle(market_stats)

        for current_timeslot, market_stat in market_stats:
            market_results_aggr.update(current_timeslot, market_stat)
        aggregated_result = list(market_results_aggr.generate())

        assert len(aggregated_result) == 1
        assert aggregated_result[0]["start_time"] == next_time

        # and the buffer should be empty now
        assert len(market_results_aggr.bids_offers_trades) == 0

    def test_no_results_are_returned_if_timeslots_are_not_enough(self):
        """Test that calling generate with insufficient amount of data
        will not return any result."""

        resolution = duration(days=1)
        market_results_aggr = MarketResultsAggregator(
            resolution=resolution,
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        slot_length = duration(minutes=15)
        market_stats_gen = self.gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=slot_length)

        needed_data_points = int(resolution.total_seconds() / slot_length.total_seconds())
        for _ in range(needed_data_points - 1):
            market_results_aggr.update(*next(market_stats_gen))

        assert len(list(market_results_aggr.generate())) == 0
        # given 1 more slot data, the generator should yield 1 result.
        market_results_aggr.update(*next(market_stats_gen))
        assert len(list(market_results_aggr.generate())) == 1

    def test_market_results_aggr_raises_when_some_timeslots_are_missing(self):
        """Test time difference between collected timeslots is exactly one slot length."""
        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        market_stats_gen = self.gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=Duration(minutes=15))

        for _ in range(3):
            market_results_aggr.update(*next(market_stats_gen))

        next(market_stats_gen)  # missing timeslot
        market_results_aggr.update(*next(market_stats_gen))

        try:
            # this should raise an AssertionError
            list(market_results_aggr.generate())
            pytest.fail(
                "MarketResultsAggregator should not process insufficient number of data points.")
        except AssertionError:
            pass
