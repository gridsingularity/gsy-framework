"""Module for parsing SCM Community Datasheet Excel files."""

import json
from collections import defaultdict
from itertools import chain

from openpyxl import load_workbook

from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.sheet_parsers import (
    CommunityMembersSheetParser, GeneralSettingsSheetParser, LoadSheetParser, ProfileSheetParser,
    PVSheetParser, StorageSheetParser)

PROFILE_KEYS_BY_TYPE = {
    "Load": "daily_load_profile",
    "PV": "power_profile",
    "SmartMeter": "smart_meter_profile"
}


class CommunityDatasheetParser:
    """Parser for Community Datasheet files."""

    SHEETNAMES = {"General settings", "Community Members", "Load", "PV", "Storage", "Profiles"}

    def __init__(self, filename):
        self._filename = filename

    def parse(self):
        """Parse the entire datasheet."""
        workbook = load_workbook(self._filename)
        current_sheetnames = set(workbook.sheetnames)
        if not current_sheetnames == self.SHEETNAMES:
            raise CommunityDatasheetException(
                f"The datasheet should contain the following sheets: {self.SHEETNAMES}."
                f"Found: {current_sheetnames}.")

        members_to_loads = LoadSheetParser(workbook["Load"]).parse()
        members_to_pvs = PVSheetParser(workbook["PV"]).parse()
        members_to_storages = StorageSheetParser(workbook["Storage"]).parse()

        # Merge the 3 dictionaries by their key "Member_name"
        dict_items = [d.items() for d in [members_to_loads, members_to_pvs, members_to_storages]]
        members_to_assets = defaultdict(list)
        for member_name, assets in chain.from_iterable(dict_items):
            members_to_assets[member_name].extend(assets)

        print(json.dumps(members_to_assets, indent=4))
        members_to_details = CommunityMembersSheetParser(workbook["Community Members"]).parse()
        print(json.dumps(members_to_details, indent=4))

        if any((missing := member) not in members_to_details for member in members_to_assets):
            raise CommunityDatasheetException(
                f'Member "{missing}" was defined in one of the asset sheets'  # noqa: F821
                'but not in the "Community Members" sheet.')

        # - [ ] Put the 3 dicts together to create a grid structure

        # Parse the profile sheet
        profiles = ProfileSheetParser(workbook["Profiles"]).parse()
        print(json.dumps(profiles, indent=4))

        self._merge_profiles_into_assets(profiles, members_to_assets)
        print(json.dumps(members_to_assets, indent=4))

        # Parse the general settings sheet
        settings = GeneralSettingsSheetParser(workbook["General settings"]).parse()
        print(json.dumps(settings, indent=4))

    @staticmethod
    def _merge_profiles_into_assets(profiles, members_to_assets):
        """Merge each energy profile into the representation of its own asset."""
        for asset in chain.from_iterable(members_to_assets.values()):
            asset_name = asset["name"]
            if asset_name not in profiles:
                continue
            asset_type = asset["type"]
            try:
                profile_key = PROFILE_KEYS_BY_TYPE[asset_type]
            except KeyError as ex:
                raise CommunityDatasheetException(
                    f'Asset type "{asset_type}" is not supported.') from ex
            asset[profile_key] = profiles[asset_name]


def parse_community_datasheet(filename):
    """Parse the content of the community datasheet and return a JSON representation."""
    CommunityDatasheetParser(filename).parse()


if __name__ == "__main__":
    parse_community_datasheet(
        "/Users/fievelk/Code/work/grid_singularity/Community_DataSheet_v2_ppp.xlsx")
