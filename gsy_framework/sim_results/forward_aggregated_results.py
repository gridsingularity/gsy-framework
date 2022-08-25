from typing import Callable, Dict, List

from pendulum import DateTime, Duration


class MarketResultsAggregator:
    """Calculate aggregated/accumulated market results in different resolutions."""

    def __init__(self, resolution: Duration,  # pylint: disable=too-many-arguments
                 simulation_slot_length: Duration,
                 last_aggregated_result: Dict = None,
                 aggregators: Dict[str, Callable] = None,
                 accumulators: Dict[str, Callable] = None):
        """
        - Aggregators are applied to collected raw data of each aggregation window.
        Each aggregator function accepts one argument which is in the form of a dictionary
        containing bids, offers and trades.
        Here's an example of aggregators dictionary:
        aggregators = {
            "device_statistics": device_statistics_aggregator,
            "energy_traded_profile": energy_traded_profile_aggregator
        }
        - Accumulators are applied to collected raw data of the current aggregation window
        as well as the results from last calculation. And, they are written in a `reduce` manner.
        Each accumulator function accepts two arguments which are the previously calculated data
        of the same function and collected raw data of the current aggregation windows.
        Here's an example of accumulators dictionary:
        accumulators = {
            "device_statistics": device_statistics_accumulator,
            "energy_traded_profile": energy_traded_profile_accumulator
        }
        """

        self.bids_offers_trades: Dict[DateTime, Dict] = {}
        self.last_aggregated_result = last_aggregated_result if \
            last_aggregated_result is not None else {}
        self.resolution = resolution
        self.simulation_slot_length = simulation_slot_length
        self.aggregators = aggregators if aggregators else {}
        self.accumulators = accumulators if accumulators else {}

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

    def generate(self):
        """Generate aggregated/accumulated results in the specified resolution from the
        raw results. If the given resolution is smaller than the timedelta between consequent
        market slots, then the same data will be returned.
        """
        if not self.bids_offers_trades:
            return

        sorted_market_timeslots = sorted(self.bids_offers_trades)
        start_time = sorted_market_timeslots[0]
        next_time = start_time + self.resolution
        timeslots_to_aggregate = []
        for timeslot in sorted_market_timeslots:
            if timeslot >= next_time:
                if timeslots_to_aggregate:
                    self._check_timeslots(timeslots_to_aggregate)
                    yield self._prepare_results(timeslots_to_aggregate)
                    self._remove_processed_timeslots(timeslots_to_aggregate)
                    timeslots_to_aggregate = []
                timeslots_to_aggregate.append(timeslot)
                next_time += self.resolution
            else:
                timeslots_to_aggregate.append(timeslot)

    def _remove_processed_timeslots(self, timeslots: List[DateTime]):
        """Remove already processed timeslots from the buffer to save some memory."""
        for timeslot in timeslots:
            del self.bids_offers_trades[timeslot]

    def _check_timeslots(self, timeslots_to_aggregate: List[DateTime]):
        """Perform sanity checks on timeslots to avoid issues while
        aggregating or accumulating results."""

        window_start_time = timeslots_to_aggregate[0]
        window_end_time = window_start_time + self.resolution
        number_of_required_timeslots = 0
        while window_start_time < window_end_time:
            number_of_required_timeslots += 1
            window_start_time += self.simulation_slot_length

        assert len(timeslots_to_aggregate) == number_of_required_timeslots, \
            "Invalid aggregation resolution or insufficient number of data points."

        if not self.last_aggregated_result:
            return
        # time difference between the last result and the current one should be equal to
        # 1 duration. otherwise, it's obvious that some data is missing in the calculation.
        last_time = timeslots_to_aggregate[0] - self.resolution
        assert last_time == self.last_aggregated_result["start_time"], \
            "Invalid last_aggregated_result provided."

    def _prepare_results(self, timeslots: List[DateTime]):
        """Call all the aggregation/accumulation functions on the grouped timeslots data."""
        # This part can be compromised for more performance.
        # An accumulator/aggregator could be also passed the timeslots lists
        # and the bids_offers_trades buffer to process the current results.
        collected_raw_data = {"bids": [], "offers": [], "trades": []}
        for timeslot in timeslots:
            for order, collected_order in collected_raw_data.items():
                collected_order.extend(self.bids_offers_trades[timeslot][order])

        result = {
            "start_time": timeslots[0],
            "aggregated_results": self._aggregated_results(collected_raw_data),
            "accumulated_results": self._accumulated_results(collected_raw_data)
        }
        self.last_aggregated_result = result
        return result

    def _aggregated_results(self, collected_raw_data: Dict) -> Dict:
        """Call all the aggregator functions to calculate results for the
        selected time window e.g. resolution"""
        aggregated_results = {}
        for aggregator_name, aggregator_fn in self.aggregators.items():
            aggregated_results[aggregator_name] = aggregator_fn(collected_raw_data)
        return aggregated_results

    def _accumulated_results(self, collected_raw_data: Dict) -> Dict:
        """Call all the accumulator functions to update global statistics of the whole market.
        Accumulated results are results calculated from the beginning of the simulation.
        """
        last_accumulated_results = self.last_aggregated_result.get(
            "accumulated_results", {})

        accumulated_results = {}
        for accumulator_name, accumulator in self.accumulators.items():
            accumulated_results[accumulator_name] = accumulator(
                last_accumulated_results.get(accumulator_name), collected_raw_data)
        return accumulated_results


class AggregationTimeManager:
    """Check if any aggregation is required for any given timeslot."""
    def __init__(self, simulation_start_time: DateTime):
        self.simulation_start_time = simulation_start_time

    def get_aggregation_windows(self, current_time: DateTime, resolution: Duration,
                                last_aggregation_time: DateTime = None) -> List:
        """Check if any aggregation is required for the market."""
        aggregation_windows = []
        if last_aggregation_time is None:
            next_aggregation_time = self.simulation_start_time + resolution
        else:
            next_aggregation_time = last_aggregation_time + resolution

        while next_aggregation_time <= current_time:
            aggregation_windows.append(
                {"start_time": next_aggregation_time - resolution,
                 "end_time": next_aggregation_time})
            next_aggregation_time += resolution

        return aggregation_windows
