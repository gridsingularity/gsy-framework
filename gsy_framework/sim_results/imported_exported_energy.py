from collections import defaultdict
from typing import Dict

from gsy_framework.sim_results.results_abc import ResultsBaseClass
from gsy_framework.utils import add_or_create_key, HomeRepresentationUtils

ENERGY_STAT_FIELDS = {
    "imported_from_community",
    "imported_from_grid",
    "exported_to_community",
    "exported_to_grid",
}


class ImportedExportedEnergyHandler(ResultsBaseClass):
    """Class that calculates imported and exported energy results"""

    _market_slot: str

    def __init__(self, should_export_plots: bool):
        self._init_results_dict()
        self.should_export_plots = should_export_plots
        self.key_str = "name" if self.should_export_plots else "uuid"

    # pylint: disable=arguments-renamed
    def update(self, area_dict: Dict, core_stats: Dict, _current_market_slot):
        self._market_slot = _current_market_slot

        if not self.should_export_plots:
            # do not accumulate over timestamps for the gsy-web path
            self._init_results_dict()
        for child_dict in area_dict["children"]:
            # loop over all communities
            if not child_dict.get("children"):
                continue
            if _current_market_slot != "":
                self._accumulate_imported_exported_energy(child_dict, core_stats)

    def memory_allocation_size_kb(self):
        return self._calculate_memory_allocated_by_objects([self.imported_exported_energy])

    @staticmethod
    def merge_results_to_global(market_device: Dict, global_device: Dict, *_):
        # pylint: disable=arguments-differ
        raise NotImplementedError(
            "Cumulative grid trades endpoint supports only global results, merge not supported."
        )

    @property
    def raw_results(self):
        return self.imported_exported_energy

    def restore_area_results_state(self, area_dict: Dict, last_known_state_data: Dict):
        """No need for this as no state is needed"""

    def _init_results_dict(self):
        self.imported_exported_energy: Dict[str, Dict[str, float]] = defaultdict(dict)

    def _prepopulate_results_dict_with_zeros(self, member_uuid_name_mapping: Dict):
        members = (
            member_uuid_name_mapping.values()
            if self.should_export_plots
            else member_uuid_name_mapping.keys()
        )
        for member_key in members:
            if member_key not in self.imported_exported_energy:
                self.imported_exported_energy[member_key] = {}

            if self._market_slot not in self.imported_exported_energy[member_key]:
                self.imported_exported_energy[member_key][self._market_slot] = {}

            for stat_key in ENERGY_STAT_FIELDS:
                if stat_key not in self.imported_exported_energy[member_key][self._market_slot]:
                    self.imported_exported_energy[member_key][self._market_slot][stat_key] = 0

    def _accumulate_imported_exported_energy(self, community_dict: Dict, core_stats: Dict):
        community_uuid = community_dict["uuid"]
        community_trades = core_stats.get(community_uuid, {}).get("trades", [])
        member_uuid_name_mapping = HomeRepresentationUtils.get_member_uuid_name_mapping(
            community_dict
        )
        # Adding community name and uuid to the member uuid name mapping to include it in the
        # imported exported results
        self._prepopulate_results_dict_with_zeros(
            {**member_uuid_name_mapping, community_uuid: community_dict["name"]}
        )
        community_member_uuids = member_uuid_name_mapping.keys()
        member_key = "name" if self.should_export_plots else "uuid"
        community_key = community_dict["name"] if self.should_export_plots else community_uuid
        for trade in community_trades:
            if (
                trade["buyer"]["uuid"] in community_member_uuids
                and trade["seller"]["uuid"] in community_member_uuids
            ):
                add_or_create_key(
                    self.imported_exported_energy[trade["buyer"][member_key]][self._market_slot],
                    "imported_from_community",
                    trade["energy"],
                )
                add_or_create_key(
                    self.imported_exported_energy[trade["seller"][member_key]][self._market_slot],
                    "exported_to_community",
                    trade["energy"],
                )

            elif (
                trade["buyer"]["uuid"] in community_member_uuids
                and trade["seller"]["uuid"] == community_uuid
            ):
                add_or_create_key(
                    self.imported_exported_energy[trade["buyer"][member_key]][self._market_slot],
                    "imported_from_grid",
                    trade["energy"],
                )
                # Track community imported energy from grid
                add_or_create_key(
                    self.imported_exported_energy[community_key][self._market_slot],
                    "imported_from_grid",
                    trade["energy"],
                )
            elif (
                trade["seller"]["uuid"] in community_member_uuids
                and trade["buyer"]["uuid"] == community_uuid
            ):
                add_or_create_key(
                    self.imported_exported_energy[trade["seller"][member_key]][self._market_slot],
                    "exported_to_grid",
                    trade["energy"],
                )
                # Track community exported energy to grid
                add_or_create_key(
                    self.imported_exported_energy[community_key][self._market_slot],
                    "exported_to_grid",
                    trade["energy"],
                )
