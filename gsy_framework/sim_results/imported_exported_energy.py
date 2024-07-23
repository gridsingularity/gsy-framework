from collections import defaultdict
from typing import Dict

from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import add_or_create_key


class ImportedExportedEnergyHandler(ResultsBaseClass):
    """Class that calculates imported and exported energy results"""

    def __init__(self):
        self.imported_exported_energy: Dict[str, Dict[str, float]] = defaultdict(dict)

    # pylint: disable=arguments-renamed
    def update(self, area_dict: Dict, core_stats: Dict, _current_market_slot):

        for child_dict in area_dict["children"]:
            # loop over all communities
            if not child_dict.get("children"):
                continue
            self._accumulate_imported_exported_energy(child_dict, core_stats)

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([self.imported_exported_energy])

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        # pylint: disable=arguments-differ
        raise NotImplementedError(
            "Cumulative grid trades endpoint supports only global results," " merge not supported."
        )

    @property
    def raw_results(self):
        return self.imported_exported_energy

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """No need for this as no state is needed"""

    @staticmethod
    def _get_community_member_uuids(community_dict: Dict):
        community_member_uuids = []
        for child_dict in community_dict["children"]:
            if not child_dict.get("children"):
                continue
            community_member_uuids.append(child_dict["uuid"])
        return community_member_uuids

    def _accumulate_imported_exported_energy(self, community_dict: Dict, core_stats: Dict):
        community_trades = core_stats.get(community_dict["uuid"], {}).get("trades", [])
        community_member_uuids = self._get_community_member_uuids(community_dict)
        for trade in community_trades:
            if (
                trade["buyer"]["uuid"] in community_member_uuids
                and trade["seller"]["uuid"] in community_member_uuids
            ):
                add_or_create_key(
                    self.imported_exported_energy[trade["buyer"]["uuid"]],
                    "imported_from_community",
                    trade["energy"],
                )
                add_or_create_key(
                    self.imported_exported_energy[trade["seller"]["uuid"]],
                    "exported_to_community",
                    trade["energy"],
                )
            elif (
                trade["buyer"]["uuid"] in community_member_uuids
                and trade["seller"]["uuid"] not in community_member_uuids
            ):
                add_or_create_key(
                    self.imported_exported_energy[trade["buyer"]["uuid"]],
                    "imported_from_grid",
                    trade["energy"],
                )
            elif (
                trade["seller"]["uuid"] in community_member_uuids
                and trade["buyer"]["uuid"] not in community_member_uuids
            ):
                add_or_create_key(
                    self.imported_exported_energy[trade["seller"]["uuid"]],
                    "exported_to_grid",
                    trade["energy"],
                )
            else:
                raise AssertionError("Should never reach this point")
