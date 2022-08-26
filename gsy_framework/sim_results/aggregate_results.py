"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from datetime import date, timedelta  # NOQA
from typing import Callable, Dict, List

from pendulum import DateTime, Duration

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.sim_results.area_throughput_stats import AreaThroughputStats
from gsy_framework.sim_results.device_statistics import DeviceStatistics
from gsy_framework.sim_results.energy_trade_profile import EnergyTradeProfile
from gsy_framework.sim_results.market_price_energy_day import \
    MarketPriceEnergyDay
from gsy_framework.sim_results.market_summary_info import MarketSummaryInfo

REQUESTED_FIELDS_LIST = ["price_energy_day", "device_statistics",
                         "energy_trade_profile", "area_throughput", "market_summary"]


REQUESTED_FIELDS_CLASS_MAP = {
    "price_energy_day": MarketPriceEnergyDay,
    "device_statistics": DeviceStatistics,
    "energy_trade_profile": EnergyTradeProfile,
    "area_throughput": AreaThroughputStats,
    "market_summary": MarketSummaryInfo
}

# Used by forward markets; the following dictionary defines
# what aggregations are needed for each market type.
MARKET_RESOLUTIONS = {
    AvailableMarketTypes.YEAR_FORWARD: [AggregationResolution.RES_1_MONTH],
    AvailableMarketTypes.MONTH_FORWARD: [AggregationResolution.RES_1_DAY],
    AvailableMarketTypes.WEEK_FORWARD: [AggregationResolution.RES_1_DAY]
}

# Used by MarketResultsAggregator; the following dictionary defines
# what aggregators/accumulators should be called for each resolution type.
RESOLUTION_AGGREGATIONS = {
    AggregationResolution.RES_1_MONTH: {
        "aggregators": {},
        "accumulators": {}
    },
    AggregationResolution.RES_1_DAY: {
        "aggregators": {},
        "accumulators": {}
    },
}


def merge_last_market_results_to_global(
        market_results: Dict, global_results: Dict,
        slot_list_ui_format: List = None, requested_fields: List = None
):
    """Global results are the accumulated statistics from the beginning of the simulation.
    This function updates the global results using the market results which are results of
    the current market slot.
    """

    if requested_fields is None:
        requested_fields = REQUESTED_FIELDS_LIST

    for field in requested_fields:
        global_results[field] = REQUESTED_FIELDS_CLASS_MAP[field].merge_results_to_global(
            market_results[field], global_results[field], slot_list_ui_format
        )

    return global_results


class MarketResultsAggregator:
    """Calculate aggregated/accumulated market results in different resolutions."""

    def __init__(  # pylint: disable=too-many-arguments
            self, resolution: Duration,
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

    def update(self, current_timeslot: DateTime, market_stats: Dict[str, Dict[str, List]]) -> None:
        """Update the buffer of bids_offers_trades with the result
        from the current market slot.
        Example of market stats:
        market_stats = {
            '2020-01-01T00:00:00': {'bids': [...], 'offers': [...], 'trades': [...]},
            '2020-01-01T00:15:00': {'bids': [...], 'offers': [...], 'trades': [...]},
            '2020-01-01T00:30:00': {'bids': [...], 'offers': [...], 'trades': [...]},
            ...
        }
        """
        if not market_stats:
            return

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
        next_time = start_time + self.resolution - self.simulation_slot_length
        timeslots_to_aggregate = []
        for timeslot in sorted_market_timeslots:
            if timeslot >= next_time:
                timeslots_to_aggregate.append(timeslot)
                self._check_timeslots(timeslots_to_aggregate)
                yield self._prepare_results(timeslots_to_aggregate)
                self._remove_processed_timeslots(timeslots_to_aggregate)
                timeslots_to_aggregate = []
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

    def get_aggregation_windows(
            self, current_time: DateTime, resolution: Duration,
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
