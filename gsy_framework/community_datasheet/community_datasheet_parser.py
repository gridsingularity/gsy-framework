"""Module for parsing SCM Community Datasheet Excel files."""

import copy
import logging
import uuid
from itertools import chain
from typing import Dict

import requests
from jsonschema.exceptions import ValidationError

from gsy_framework.community_datasheet.community_datasheet_reader import (
    CommunityDatasheet, CommunityDatasheetReader)
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.location_converter import (
    LocationConverter, LocationConverterException)
from gsy_framework.scenario_validators import scenario_validator

logger = logging.getLogger(__name__)

PROFILE_KEYS_BY_TYPE = {
    "Load": "daily_load_profile",
    "PV": "power_profile",
    "SmartMeter": "smart_meter_profile"
}


class CommunityDatasheetParser:
    """Parser for the community datasheet."""
    def __init__(self, datasheet: CommunityDatasheet):
        self._datasheet = copy.deepcopy(datasheet)  # Avoid modifying the original datasheet object

    def parse(self):
        """Convert the datasheet to grid-like items."""
        self._add_pv_coordinates(self._datasheet.pvs, self._datasheet.members)
        assets_by_member = self._get_assets_by_member()

        self._merge_profiles_into_assets(self._datasheet.profiles, assets_by_member)
        grid = self._create_grid(assets_by_member)

        self._validate_grid(grid)
        return {
            "settings": self._datasheet.settings,
            "grid": grid
        }

    @classmethod
    def _add_pv_coordinates(cls, pvs_by_member: Dict, members_information: Dict):
        try:
            location_converter = LocationConverter()
        except LocationConverterException as ex:
            logger.warning(ex)
            return

        with requests.Session() as session:
            for member_name, pv_assets in pvs_by_member.items():
                coordinates = cls._get_member_coordinates(
                    members_information[member_name],
                    location_converter=location_converter,
                    session=session)
                for pv_details in pv_assets:
                    pv_details["geo_tag_location"] = coordinates

    @staticmethod
    def _get_member_coordinates(
            member_details: Dict, location_converter: LocationConverter, session=None):
        address = member_details["Location/Address (optional)"] or ""
        zip_code = member_details["ZIP code"] or ""
        full_address = f"{address} {zip_code}"
        if not full_address.strip():
            return None

        try:
            return location_converter.convert(full_address, session=session)
        except LocationConverterException as ex:
            raise CommunityDatasheetException(ex) from ex

    @staticmethod
    def _validate_grid(grid):
        try:
            scenario_validator(grid)
        except ValidationError as ex:
            raise CommunityDatasheetException(ex) from ex

    def _get_assets_by_member(self) -> Dict:
        """Return a mapping between each member and their assets."""
        assets_by_member = {member_name: [] for member_name in self._datasheet.members}
        asset_items = [
            assets.items()
            for assets in [self._datasheet.loads, self._datasheet.pvs, self._datasheet.storages]
        ]
        for member_name, assets in chain.from_iterable(asset_items):
            assets_by_member[member_name].extend(assets)

        if any((missing := member) not in self._datasheet.members for member in assets_by_member):
            raise CommunityDatasheetException(
                f'Member "{missing}" was defined in one of the asset sheets'  # noqa: F821
                'but not in the "Community Members" sheet.')

        return assets_by_member

    @staticmethod
    def _merge_profiles_into_assets(profiles: Dict, assets_by_member: Dict) -> None:
        """Merge (in-place) each energy profile into the representation of its own asset."""
        for asset in chain.from_iterable(assets_by_member.values()):
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

    def _create_grid(self, assets_by_member: Dict) -> Dict:
        members_grid = []
        for member_name, assets in assets_by_member.items():
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

    def _create_member_representation(self, member_name: str) -> Dict:
        return {
            **self._datasheet.members[member_name],
            **{
                "name": member_name,
                "tags": ["Home"],
                "type": "Area",
                "uuid": str(uuid.uuid4()),
                "children": []
            }}


def parse_community_datasheet(filename):
    """Parse the content of the community datasheet and return a JSON representation."""
    datasheet = CommunityDatasheetReader.read(filename)
    parser = CommunityDatasheetParser(datasheet)
    print(parser.parse())


if __name__ == "__main__":
    parse_community_datasheet(
        "/Users/fievelk/Code/work/grid_singularity/Community_DataSheet_v2_ppp.xlsx")
