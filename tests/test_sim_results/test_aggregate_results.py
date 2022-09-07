from random import shuffle
from uuid import uuid4

import pytest
from pendulum import DateTime, Duration, duration

from gsy_framework.sim_results.aggregate_results import (
    AggregationTimeManager, MarketResultsAggregator)

DEFAULT_SIMULATION_SLOT_LENGTH = duration(minutes=15)
MARKET_TIMESLOTS = 10
ORDERS_PER_MARKET_SLOT = 2


def gen_market_stats(start_time: DateTime, slot_length: Duration):
    """Simulate market stats{bids,offers,trades} for each timeslot."""
    while True:
        market_stats = {}
        market_timeslot = start_time
        for _ in range(MARKET_TIMESLOTS):
            market_stats[str(market_timeslot)] = {
                "bids": [
                    {"creation_time": start_time, "timeslot": market_timeslot, "uuid": uuid4(),
                     "price": 150, "energy": 5, "buyer_id": "BUYER"}
                    for _ in range(ORDERS_PER_MARKET_SLOT)],
                "offers": [
                    {"creation_time": start_time, "timeslot": market_timeslot, "uuid": uuid4(),
                     "price": 150, "energy": 5, "seller_id": "SELLER"}
                    for _ in range(ORDERS_PER_MARKET_SLOT)],
                "trades": [
                    {"creation_time": start_time, "timeslot": market_timeslot, "uuid": uuid4(),
                     "price": 30, "energy": 1, "seller_id": "SELLER", "buyer_id": "BUYER"}
                    for _ in range(ORDERS_PER_MARKET_SLOT)]
            }
            market_timeslot += slot_length
        yield start_time, market_stats
        start_time += slot_length


class TestMarketResultsAggregator:

    @staticmethod
    def test_bids_offers_trades_buffer_gets_updated():
        """Test if bids_offers_trades buffer of the MarketResultsAggregator gets
        updated on each call to its update()/generate() method.
        Also, check that the correct number of bids/offers/trades are stored at each timeslot.
        """
        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        market_stats_gen = gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=DEFAULT_SIMULATION_SLOT_LENGTH)

        added_timeslots = []

        for _ in range(4):
            current_timeslot, market_stat = next(market_stats_gen)
            market_results_aggr.update(current_timeslot, market_stat)
            added_timeslots.append(current_timeslot)

            for order in ("bids", "offers", "trades"):
                # check correct number of orders are saved per timeslot
                assert len(
                    set(o["uuid"] for o in
                        market_results_aggr.bids_offers_trades[current_timeslot][order])
                ) == ORDERS_PER_MARKET_SLOT * MARKET_TIMESLOTS

            # check all the added timeslots are still there.
            assert all(timeslot in market_results_aggr.bids_offers_trades for
                       timeslot in added_timeslots)
            # check no extra timeslot is saved.
            assert len(market_results_aggr.bids_offers_trades) == len(added_timeslots)

        # check no duplicated entries are added for each timeslot
        for order in ("bids", "offers", "trades"):
            buff_orders = set()
            # ensure collected orders are unique and the same order is not repeatedly
            # appended as a fault.
            for market_stats in market_results_aggr.bids_offers_trades.values():
                buff_orders = buff_orders.union(set(o["uuid"] for o in market_stats[order]))
            assert len(buff_orders) == 4 * MARKET_TIMESLOTS * ORDERS_PER_MARKET_SLOT

        # only one result should be generated for slot_length=15m and resolution=1h.
        assert len(list(market_results_aggr.generate())) == 1
        # data should be cleared from cache once it's processed.
        assert len(market_results_aggr.bids_offers_trades) == 0

    @staticmethod
    def test_correct_timeslots_are_being_consumed():
        """Test that correct consequent timeslots are being consumed and
        others remain unused in the buffer. Also, make sure that the
        order of updates doesn't affect the final result."""

        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        simulation_start_time = DateTime(2020, 1, 1, 0, 0)
        market_stats_gen = gen_market_stats(
            simulation_start_time, slot_length=DEFAULT_SIMULATION_SLOT_LENGTH)

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

    @staticmethod
    def test_no_results_are_returned_if_timeslots_are_not_enough():
        """Test that calling generate with insufficient amount of data
        will not return any result."""

        resolution = duration(days=1)
        market_results_aggr = MarketResultsAggregator(
            resolution=resolution,
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        market_stats_gen = gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=DEFAULT_SIMULATION_SLOT_LENGTH)

        needed_data_points = int(resolution.total_seconds() /
                                 DEFAULT_SIMULATION_SLOT_LENGTH.total_seconds())
        for _ in range(needed_data_points - 1):
            market_results_aggr.update(*next(market_stats_gen))

        assert len(list(market_results_aggr.generate())) == 0
        # given 1 more slot data, the generator should yield 1 result.
        market_results_aggr.update(*next(market_stats_gen))
        assert len(list(market_results_aggr.generate())) == 1

    @staticmethod
    def test_market_results_aggr_raises_when_some_timeslots_are_missing():
        """Test time difference between collected timeslots is exactly one slot length."""
        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH
        )
        market_stats_gen = gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=DEFAULT_SIMULATION_SLOT_LENGTH)

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

    @staticmethod
    def test_all_consumed_timeslots_are_given_to_aggregators_and_accumulators():
        """Test timeslots are correctly grouped and then passed to accumulators/aggregators."""

        def check_collected_raw_data(collected_raw_data):
            collected_time_slots = set(
                bid["creation_time"] for bid in collected_raw_data["bids"]
            )
            assert len(collected_time_slots) == 4
            assert min(collected_time_slots) == simulation_start_time
            assert max(collected_time_slots) - min(collected_time_slots) < duration(hours=1)

            collected_time_slots = set(
                bid["creation_time"] for bid in collected_raw_data["offers"]
            )
            assert len(collected_time_slots) == 4
            assert min(collected_time_slots) == simulation_start_time
            assert max(collected_time_slots) - min(collected_time_slots) < duration(hours=1)

            collected_time_slots = set(
                bid["creation_time"] for bid in collected_raw_data["trades"]
            )
            assert len(collected_time_slots) == 4
            assert min(collected_time_slots) == simulation_start_time
            assert max(collected_time_slots) - min(collected_time_slots) < duration(hours=1)

        def aggregator(collected_raw_data):
            check_collected_raw_data(collected_raw_data)
            return "AGGREGATED_RESULTS"

        def accumulator(last_result, collected_raw_data):
            assert last_result is None
            check_collected_raw_data(collected_raw_data)
            return "ACCUMULATED_RESULTS"

        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH,
            aggregators={"aggr1": aggregator},
            accumulators={"accu1": accumulator}
        )
        simulation_start_time = DateTime(2020, 1, 1, 0, 0)
        market_stats_gen = gen_market_stats(
            simulation_start_time, slot_length=DEFAULT_SIMULATION_SLOT_LENGTH)

        for _ in range(7):  # accu1/aggr1 should be called only once when calling generate
            market_results_aggr.update(*next(market_stats_gen))

        result = list(market_results_aggr.generate())[0]
        assert result["aggregated_results"]["aggr1"] == "AGGREGATED_RESULTS"
        assert result["accumulated_results"]["accu1"] == "ACCUMULATED_RESULTS"
        assert result["start_time"] == simulation_start_time

    @staticmethod
    def test_invalid_resolution():
        """Test the MarketResultsAggregator can detect invalid resolutions."""
        try:
            MarketResultsAggregator(
                resolution=duration(hours=1),
                simulation_slot_length=duration(hours=2)
            )
            pytest.fail("MarketResultsAggregator fails to detect invalid resolutions.")
        except AssertionError:
            pass

    @staticmethod
    def test_leap_year():
        """Test 2020 as a leap year."""
        market_results_aggr = MarketResultsAggregator(
            resolution=duration(months=1),
            simulation_slot_length=duration(days=1)
        )
        simulation_start_time = DateTime(2020, 2, 1, 0, 0)
        market_stats_gen = gen_market_stats(
            simulation_start_time, slot_length=duration(days=1))

        market_timeslot, market_stat = next(market_stats_gen)
        while market_timeslot.month != 3:
            market_results_aggr.update(market_timeslot, market_stat)
            market_timeslot, market_stat = next(market_stats_gen)

        assert len(market_results_aggr.bids_offers_trades) == 29
        assert len(list(market_results_aggr.generate())) == 1
        assert len(market_results_aggr.bids_offers_trades) == 0

    @staticmethod
    def test_accumulator_functionality():
        """Test last_aggregated_result is being passed to the accumulator."""
        def accumulator(last_results, collected_raw_data):
            assert collected_raw_data
            return 1 if last_results is None else last_results + 1

        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH,
            accumulators={
                "accu1": accumulator
            }
        )
        market_stats_gen = gen_market_stats(
            DateTime(2020, 1, 1, 0, 0), slot_length=DEFAULT_SIMULATION_SLOT_LENGTH)

        for _ in range(4):
            market_results_aggr.update(*next(market_stats_gen))

        last_aggregated_result = list(market_results_aggr.generate())[0]
        market_results_aggr = MarketResultsAggregator(
            resolution=duration(hours=1),
            simulation_slot_length=DEFAULT_SIMULATION_SLOT_LENGTH,
            accumulators={
                "accu1": accumulator
            },
            last_aggregated_result=last_aggregated_result
        )
        for _ in range(8):
            market_results_aggr.update(*next(market_stats_gen))

        generated_results = list(market_results_aggr.generate())
        assert generated_results[0]["accumulated_results"]["accu1"] == 2
        assert generated_results[1]["accumulated_results"]["accu1"] == 3


class TestAggregationTimeManager:
    @staticmethod
    def test_aggregation_window_generator_works_correctly():
        simulation_start_time = DateTime(2020, 2, 1, 0, 0)
        resolution = duration(hours=1)
        current_time = simulation_start_time + resolution

        atm = AggregationTimeManager(simulation_start_time)
        # Make sure that only one windows is generated when it's time.
        generated_windows = atm.get_aggregation_windows(
            resolution=resolution, current_time=current_time)
        assert len(generated_windows) == 1
        assert generated_windows[0]["end_time"] - generated_windows[0]["start_time"] == resolution

        # Make sure that generated windows are consequent to each other and length of
        # each one is exactly 1 resolution.
        generated_windows = atm.get_aggregation_windows(
            resolution=resolution, current_time=simulation_start_time + duration(months=1),
            last_aggregation_time=simulation_start_time
        )
        assert len(generated_windows) == 29 * 24  # Feb 2020 has 29 days, each day 24 hours
        assert generated_windows[0]["start_time"] == simulation_start_time
        for i in range(len(generated_windows) - 1):
            assert (generated_windows[i]["end_time"] - generated_windows[i]["start_time"]
                    == resolution)
            assert generated_windows[i]["end_time"] == generated_windows[i+1]["start_time"]

    @staticmethod
    def test_no_window_is_generated_when_is_not_time():
        """Make sure that no window is generated when the end of the window is not reached yet."""
        simulation_start_time = DateTime(2020, 2, 1, 0, 0)
        resolution = duration(hours=1)
        current_time = simulation_start_time + duration(minutes=30)

        atm = AggregationTimeManager(simulation_start_time)
        generated_windows = atm.get_aggregation_windows(
            resolution=resolution, current_time=current_time)
        assert len(generated_windows) == 0
