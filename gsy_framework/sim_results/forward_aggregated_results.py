from typing import Callable, Dict, List

from pendulum import DateTime, Duration


class MarketResultsAggregator:
    """Calculate aggregated market results in different resolutions."""

    def __init__(self):
        self.bids_offers_trades: Dict[DateTime, Dict] = {}

    def update(self, current_timeslot: DateTime, market_stats) -> None:
        """Update the buffer of bids_offers_trades with the result
        from the current market slot."""
        if not market_stats:
            return

        if current_timeslot not in self.bids_offers_trades:
            self.bids_offers_trades[current_timeslot] = {
                "bids": [], "offers": [], "trades": []}

        for market_data in market_stats.values():
            for order in self.bids_offers_trades[current_timeslot]:
                self.bids_offers_trades[current_timeslot][order].extend(market_data[order])

    def generate(self, resolution: Duration, aggregators: Dict[str, Callable] = None):
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
                    yield self._aggregated_results(timeslots_to_aggregate, aggregators)
                    timeslots_to_aggregate = []
                timeslots_to_aggregate.append(timeslot)
                next_time += resolution
            else:
                timeslots_to_aggregate.append(timeslot)

    def _aggregated_results(self, timeslots: List[DateTime], aggregators):
        """Call all the aggregation function on the grouped timeslots data."""
        if aggregators is None:
            aggregators = {}

        collected_data = {"bids": [], "offers": [], "trades": []}
        for timeslot in timeslots:
            for order, collected_order in collected_data.items():
                collected_order.extend(self.bids_offers_trades[timeslot][order])

        result = {}
        for aggregator_name, aggregator_fn in aggregators.items():
            result[aggregator_name] = aggregator_fn(collected_data)

        return {
            "start_time": timeslots[0],
            **result
        }


class MarketResultsHandler:
    """Keep track of all (area, market_type) aggregated results by utilizing an
    instance of the MarketResultsHandler for each of them."""

    AVAILABLE_RESOLUTIONS: Dict[str, Duration] = {}
    RESOLUTION_AGGREGATORS: Dict[Duration, Dict[str, Callable]] = {}

    def __init__(self):
        self.markets: Dict[str, Dict[str, MarketResultsAggregator]] = {}

    def update(self, area_uuid: str, market_type: str, current_timeslot: str, market_stats):
        """Update the corresponding MarketResultsAggregator for each (area, market_type)."""
        if not market_stats:
            return

        if area_uuid not in self.markets:
            self.markets[area_uuid] = {}

        if market_type not in self.markets[area_uuid]:
            self.markets[area_uuid][market_type] = MarketResultsAggregator()

        current_timeslot = DateTime.fromisoformat(current_timeslot)
        self.markets[area_uuid][market_type].update(current_timeslot, market_stats)

    def generate(self):
        """Generate the appropriate aggregated results for each (area, market_type)."""
        for area_uuid, markets in self.markets.items():
            for market_type, market_results_aggregator in markets.items():
                for resolution in self.AVAILABLE_RESOLUTIONS.get(market_type, []):
                    aggregators = self.RESOLUTION_AGGREGATORS.get(resolution)
                    for aggregated_results in market_results_aggregator.generate(resolution,
                                                                                 aggregators):
                        yield {
                            "area_uuid": area_uuid,
                            "market_type": market_type,
                            "resolution": resolution,
                            **aggregated_results
                        }
