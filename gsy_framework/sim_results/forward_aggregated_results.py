from typing import Callable, Dict, List

from pendulum import DateTime, Duration


class MarketResultsAggregator:
    """Calculate aggregated market results in different resolutions."""

    def __init__(self, last_aggregated_result=None):
        self.bids_offers_trades: Dict[DateTime, Dict] = {}
        self.last_aggregated_result = last_aggregated_result if \
            last_aggregated_result is not None else {}

    def update(self, current_timeslot: DateTime, market_stats) -> None:
        """Update the buffer of bids_offers_trades with the result
        from the current market slot."""
        if not market_stats:
            return

        if current_timeslot not in self.bids_offers_trades:
            self.bids_offers_trades[current_timeslot] = {
                "bids": [], "offers": [], "trades": [],
            }

        for market_data in market_stats.values():
            for order in self.bids_offers_trades[current_timeslot]:
                self.bids_offers_trades[current_timeslot][order].extend(market_data[order])

    def generate(self, resolution: Duration,
                 aggregators: Dict[str, Callable] = None,
                 accumulators: Dict[str, Callable] = None):
        """Generate aggregated results in the specified resolution from the raw results.
        If no resolution is given, then the data in its original resolution will be aggregated.
        If the resolution is smaller than the timedelta between consequent, then the same data
        will be returned.
        """
        if not self.bids_offers_trades:
            return

        sorted_market_timeslots = sorted(self.bids_offers_trades)
        start_time = sorted_market_timeslots[0]
        next_time = start_time + resolution
        timeslots_to_aggregate = []
        for timeslot in sorted_market_timeslots:
            if timeslot >= next_time:
                if timeslots_to_aggregate:
                    yield self._aggregated_results(timeslots_to_aggregate,
                                                   aggregators, accumulators)
                    self._remove_processed_timeslots(timeslots_to_aggregate)
                    timeslots_to_aggregate = []
                timeslots_to_aggregate.append(timeslot)
                next_time += resolution
            else:
                timeslots_to_aggregate.append(timeslot)

    def _remove_processed_timeslots(self, timeslots: List[DateTime]):
        """Remove already processed timeslots from the buffer to save some memory."""
        for timeslot in timeslots:
            del self.bids_offers_trades[timeslot]

    def _aggregated_results(self, timeslots: List[DateTime], aggregators, accumulators):
        """Call all the aggregation function on the grouped timeslots data."""
        if aggregators is None:
            aggregators = {}

        collected_data = {"bids": [], "offers": [], "trades": []}
        for timeslot in timeslots:
            for order, collected_order in collected_data.items():
                collected_order.extend(self.bids_offers_trades[timeslot][order])

        aggregated_results = {}
        for aggregator_name, aggregator_fn in aggregators.items():
            aggregated_results[aggregator_name] = aggregator_fn(collected_data)

        result = {
            "current_results": {
                "start_time": timeslots[0],
                **aggregated_results
            },
            "accumulated_results": self._accumulated_results(collected_data, accumulators)
        }
        self.last_aggregated_result = result
        return result

    def _accumulated_results(self, collected_data: Dict, accumulators) -> Dict:
        if accumulators is None:
            accumulators = {}

        last_accumulated_results = self.last_aggregated_result.get(
            "accumulated_results", {})

        accumulated_results = {}
        for accumulator_name, accumulator in accumulators.items():
            accumulated_results[accumulator_name] = accumulator(
                last_accumulated_results.get(accumulator_name), collected_data)
        return accumulated_results


class AggregationTimeManager:
    """Check if any aggregation is required for any given timeslot."""
    def __init__(self, simulation_start_time: DateTime,
                 simulation_slot_length: Duration,
                 market_aggregations: Dict[str, Duration]):
        self.simulation_start_time = simulation_start_time
        self.simulation_slot_length = simulation_slot_length
        self.market_aggregations = market_aggregations

    def is_time_to_aggregate(self, current_time: DateTime, market_type: str) -> List:
        """Check if any aggregation is required for the current_time."""
        aggregation_resolutions = []
        delta = current_time - self.simulation_start_time
        for aggr_duration in self.market_aggregations.get(market_type, []):
            if delta.total_seconds() % aggr_duration.total_seconds() == 0 and \
                    current_time - aggr_duration >= self.simulation_start_time:
                aggregation_resolutions.append(
                    {"start_time": current_time - aggr_duration,
                     "end_time": current_time, "resolution": aggr_duration})

        return aggregation_resolutions
