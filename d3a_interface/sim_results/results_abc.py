from abc import ABC, abstractmethod
from typing import Dict, List

from d3a_interface.utils import get_json_dict_memory_allocation_size


class ResultsBaseClass(ABC):

    @staticmethod
    def _has_update_parameters(area_result_dict, core_stats, current_market_slot):
        """
        Validates the update method parameters.
        Should be used to early-return in case any one of the input parameters is empty.
        If there are no results in this market slot, or if the market slot time is malformed
        then the aggregated results should not be updated.
        """
        return area_result_dict and core_stats and current_market_slot and \
            current_market_slot != ""

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
    def update(self, area_result_dict, core_stats, current_market_slot):
        """
        Updates the simulation results with bid/offer/trade data that arrive from the
        """
        pass

    @abstractmethod
    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """
        Restores the state of the simulation results for a specific area, defined by area_uuid.
        """
        pass

    @property
    @abstractmethod
    def raw_results(self):
        """
        Retrieves the accumulated result set.
        """
        pass

    @property
    def ui_formatted_results(self):
        return self.raw_results

    @abstractmethod
    def memory_allocation_size_kb(self):
        return 0.0

    @staticmethod
    def _calculate_memory_allocated_by_objects(object_list: List) -> float:
        return sum(
            get_json_dict_memory_allocation_size(o)
            for o in object_list
        )
