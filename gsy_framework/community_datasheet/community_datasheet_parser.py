"""Module for parsing SCM Community Datasheet Excel files."""

import json
import uuid
from itertools import chain
from typing import Dict

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

        self.settings: Dict = None
        self.members: Dict = None
        self.loads: Dict = None
        self.pvs: Dict = None
        self.storages: Dict = None
        self.profiles: Dict = None

    def parse(self):
        """Parse the entire datasheet."""
        workbook = load_workbook(self._filename)
        current_sheetnames = set(workbook.sheetnames)
        if not current_sheetnames == self.SHEETNAMES:
            raise CommunityDatasheetException(
                f"The datasheet should contain the following sheets: {self.SHEETNAMES}."
                f"Found: {current_sheetnames}.")

        self.settings = GeneralSettingsSheetParser(workbook["General settings"]).parse()
        self.members = CommunityMembersSheetParser(workbook["Community Members"]).parse()
        self._parse_asset_sheets(workbook)
        self.profiles = ProfileSheetParser(workbook["Profiles"]).parse()

        members_to_assets = {member_name: [] for member_name in self.members}
        asset_items = [d.items() for d in [self.loads, self.pvs, self.storages]]
        for member_name, assets in chain.from_iterable(asset_items):
            members_to_assets[member_name].extend(assets)

        if any((missing := member) not in self.members for member in members_to_assets):
            raise CommunityDatasheetException(
                f'Member "{missing}" was defined in one of the asset sheets'  # noqa: F821
                'but not in the "Community Members" sheet.')

        self._merge_profiles_into_assets(self.profiles, members_to_assets)
        # print(json.dumps(members_to_assets, indent=4))

        # Convert each member into its grid representation
        grid = self._create_grid(members_to_assets)

        return {
            "settings": self.settings,
            "grid": grid
        }

    def _create_grid(self, members_to_assets):
        members_grid = []
        for member_name, assets in members_to_assets.items():
            member_representation = self._create_member_representation(member_name)
            member_representation["children"] = assets
            members_grid.append(member_representation)

        return {
            "name": "Grid Market",
            "tags": None,
            "type": "Area",
            "uuid": str(uuid.uuid4()),
            "children": members_grid
        }

    def _create_member_representation(self, member_name):
        return {
            **self.members[member_name],
            **{
                "name": member_name,
                "tags": ["Home"],
                "type": "Area",
                "uuid": str(uuid.uuid4()),
                "children": []
            }}

    def _parse_asset_sheets(self, workbook):
        self.loads = LoadSheetParser(workbook["Load"]).parse()
        self.pvs = PVSheetParser(workbook["PV"]).parse()
        self.storages = StorageSheetParser(workbook["Storage"]).parse()

    @staticmethod
    def _merge_profiles_into_assets(profiles, members_to_assets) -> None:
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
    datasheet = CommunityDatasheetParser(filename)
    output = datasheet.parse()  # NOTES: change interface?

    print(json.dumps(output, indent=4))


if __name__ == "__main__":
    parse_community_datasheet(
        "/Users/fievelk/Code/work/grid_singularity/Community_DataSheet_v2_ppp.xlsx")
