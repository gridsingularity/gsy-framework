"""Module for parsing SCM Community Datasheet Excel files."""

import logging
import uuid
from enum import Enum
from itertools import chain
from typing import Dict, List

from gsy_framework import NULL_VALUES
from gsy_framework.community_datasheet.community_datasheet_reader import CommunityDatasheetReader
from gsy_framework.community_datasheet.community_datasheet_validator import (
    CommunityDatasheetValidator,
)
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.constants_limits import ConstSettings, FIELDS_REQUIRED_FOR_REBASE
from gsy_framework.enums import CloudCoverage

logger = logging.getLogger(__name__)

PROFILE_KEYS_BY_TYPE = {
    "Load": "daily_load_profile",
    "PV": "power_profile",
    "SmartMeter": "smart_meter_profile",
    "ScmStorage": "prosumption_kWh_profile",
}


class DefaultCommunityAreaNames(Enum):
    """Enum for Community names that are always part of a SCM representation."""

    GRID = "Grid"
    COMMUNITY = "Community"
    INFINITE_BUS = "InfiniteBus"


class CommunityDatasheetParser:
    """Parser for the community datasheet."""

    def __init__(self, filename):
        self._filename = filename
        self._datasheet = CommunityDatasheetReader.read(filename)

    def parse(self):
        """Parse the datasheet contents and create a grid representation."""

        self._parse_members()
        self._add_coordinates_to_assets()
        self._parse_pvs()
        self._merge_profiles_into_assets()
        self._add_global_coordinates()
        self._datasheet.grid = self._create_grid()

        CommunityDatasheetValidator().validate(self._datasheet)

        return self._datasheet

    def _add_coordinates_to_assets(self):
        for member_name, assets in self._datasheet.assets_by_member.items():
            for asset in assets:
                asset["geo_tag_location"] = self._datasheet.members[member_name][
                    "geo_tag_location"
                ]

    def _add_global_coordinates(self):
        first_member = next(iter(self._datasheet.members.values()))
        self._datasheet.global_coordinates = first_member["geo_tag_location"]

    def _parse_members(self):
        """Parse the members to add geographical coordinates."""
        for member_name, member_details in self._datasheet.members.items():
            member_details["asset_count"] = len(self._datasheet.assets_by_member[member_name])

    def _parse_pvs(self):
        pv_assets = (
            pv_asset
            for member_assets in self._datasheet.pvs.values()
            for pv_asset in member_assets
        )
        for pv_asset in pv_assets:
            pv_asset["cloud_coverage"] = self._infer_pv_cloud_coverage(pv_asset)

    def _infer_pv_cloud_coverage(self, pv_asset: Dict) -> int:
        """Infer which type of profile generation should be used."""
        asset_name = pv_asset["name"]
        # The user explicitly provided a profile for the PV
        if asset_name in self._datasheet.profiles:
            return CloudCoverage.UPLOAD_PROFILE.value

        # Each PV without profile must provide the parameters needed to call the Rebase API
        missing_attributes = [
            field for field in FIELDS_REQUIRED_FOR_REBASE if pv_asset.get(field) in NULL_VALUES
        ]

        if missing_attributes:
            raise CommunityDatasheetException(
                f'The asset "{asset_name}" does not define the following attributes: '
                f"{missing_attributes}. Either add a profile or provide all the missing fields."
            )

        return CloudCoverage.LOCAL_GENERATION_PROFILE.value

    def _merge_profiles_into_assets(self) -> None:
        """Merge (in-place) each energy profile into the representation of its own asset."""
        for asset in chain.from_iterable(self._datasheet.assets_by_member.values()):
            asset_name = asset["name"]
            if asset_name not in self._datasheet.profiles:
                continue
            asset_type = asset["type"]
            try:
                profile_key = PROFILE_KEYS_BY_TYPE[asset_type]
            except KeyError as ex:
                raise CommunityDatasheetException(
                    f'Asset type "{asset_type}" is not supported.'
                ) from ex
            asset[profile_key] = self._datasheet.profiles[asset_name]

    def _create_grid(self) -> Dict:
        grid = []
        for member_name, member_info in self._datasheet.members.items():
            assets = self._datasheet.assets_by_member[member_name]
            home_representation = self.create_home_representation(member_name, member_info, assets)
            member_info["asset_count"] = len(assets)
            grid.append(home_representation)

        return {
            "name": DefaultCommunityAreaNames.GRID.value,
            "allow_external_connection": False,
            "uuid": str(uuid.uuid4()),
            "type": "Area",
            "children": [
                {
                    "name": DefaultCommunityAreaNames.INFINITE_BUS.value,
                    "allow_external_connection": False,
                    "uuid": str(uuid.uuid4()),
                    "type": "InfiniteBus",
                    "energy_rate": ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE,
                    "energy_buy_rate": ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE,
                },
                {
                    "name": DefaultCommunityAreaNames.COMMUNITY.value,
                    "allow_external_connection": False,
                    "uuid": str(uuid.uuid4()),
                    "type": "Area",
                    "children": grid,
                },
            ],
        }

    @staticmethod
    def create_home_representation(
        member_name: str, member_info: Dict, assets: List[Dict]
    ) -> Dict:
        """Create area representation dict of the home, based on a member_info dict and assets."""
        return {
            "name": member_name,
            "tags": ["Home"],
            "type": "Area",
            "uuid": member_info["uuid"],
            "geo_tag_location": member_info["geo_tag_location"],
            "address": member_info["address"],
            "children": assets,
        }
