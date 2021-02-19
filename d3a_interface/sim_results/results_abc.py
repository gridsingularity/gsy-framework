from abc import ABC, abstractmethod
from typing import Dict, List


class ResultsBaseClass(ABC):

    @staticmethod
    def _validate_update_parameters(area_result_dict=None, core_stats=None,
                                    current_market_slot=None):
        """
        Validates the update method parameters.
        Should be used to early-return in case any one of the input parameters is empty.
        If there are no results in this market slot, or if the market slot time is malformed
        then the aggregated results should not be updated.
        """
        return not area_result_dict or not core_stats or not current_market_slot or \
            current_market_slot == ""

    @staticmethod
    @abstractmethod
    def merge_results_to_global(market_results: Dict, global_results: Dict, slot_list: List):
        """
        Merges a result set for one market to a global result set. Should be used when retrieving
        individual market data from the DB, in order to merge the individual results with the
        total requested results for a timeframe. slot_list is the list of the market slot times
        that need to be accumulated, in case this is useful for the specific result class.
        """
        pass

    @abstractmethod
    def update(self, area_result_dict=None, core_stats=None, current_market_slot=None):
        """
        Updates the simulation results with bid/offer/trade data that arrive from the
        """
        pass
