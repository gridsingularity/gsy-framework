from unittest.mock import MagicMock

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

    # TODO: tests for aggregators.
    # TODO: tests for accumulators.
    # TODO: tests correct timeslots are being grouped.
    # TODO: tests no results are being returned if not enough number of timeslots are provided.
    # TODO: tests excess amount of timeslots remain in the buffer after calling generate.
    # TODO: test invalid resolutions
    # TODO: test leap years
    # TODO: test with monthly resolutions
    # TODO: test last_aggregated_result is being applied
    # TODO: test last_aggregated_results raises error when it's incorrect
