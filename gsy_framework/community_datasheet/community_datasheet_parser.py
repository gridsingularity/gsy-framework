"""Module for parsing SCM Community Datasheet Excel files."""

import json
import logging
import uuid
from itertools import chain
from typing import Dict

import requests

from gsy_framework.community_datasheet.community_datasheet_reader import CommunityDatasheetReader
from gsy_framework.community_datasheet.community_datasheet_validator import (
    CommunityDatasheetValidator)
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.location_converter import (
    LocationConverter, LocationConverterException)
from gsy_framework.constants_limits import FIELDS_REQUIRED_FOR_REBASE
from gsy_framework.enums import CloudCoverage

logger = logging.getLogger(__name__)

PROFILE_KEYS_BY_TYPE = {
    "Load": "daily_load_profile",
    "PV": "power_profile",
    "SmartMeter": "smart_meter_profile"
}


class CommunityDatasheetParser:
    """Parser for the community datasheet."""

    def __init__(self, filename):
        self._filename = filename
        self._datasheet = CommunityDatasheetReader.read(filename)

    def parse(self):
        """Parse the datasheet contents and create a grid representation."""
        self._parse_pvs(self._datasheet.pvs, self._datasheet.members)
        assets_by_member = self._get_assets_by_member()

        self._merge_profiles_into_assets(self._datasheet.profiles, assets_by_member)
        self._datasheet.grid = self._create_grid(assets_by_member)

        CommunityDatasheetValidator().validate(self._datasheet)

        return self._datasheet

    def _parse_pvs(self, pvs_by_member: Dict, members_information: Dict):
        self._add_pv_coordinates(pvs_by_member, members_information)

        pv_assets = (
            pv_asset for member_assets in pvs_by_member.values() for pv_asset in member_assets)
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
            field for field in FIELDS_REQUIRED_FOR_REBASE if not pv_asset.get(field)]

        if missing_attributes:
            raise CommunityDatasheetException(
                f'The asset "{asset_name}" does not define the following attributes: '
                f"{missing_attributes}. Either add a profile or provide all the missing fields.")

        return CloudCoverage.LOCAL_GENERATION_PROFILE.value

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
                for pv_asset in pv_assets:
                    pv_asset["geo_tag_location"] = coordinates

    @staticmethod
    def _get_member_coordinates(
            member_details: Dict, location_converter: LocationConverter, session=None):
        address = member_details["address"] or ""
        zip_code = member_details["zip_code"] or ""
        full_address = f"{address} {zip_code}"
        if not full_address.strip():
            return None

        try:
            return location_converter.convert(full_address, session=session)
        except LocationConverterException as ex:
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
        member = self._datasheet.members[member_name]
        return {
            "name": member_name,
            "tags": ["Home"],
            "type": "Area",
            "uuid": str(uuid.uuid4()),
            "market_maker_rate": member["market_maker_rate"],
            "feed_in_tariff": member["feed_in_tariff"],
            "grid_fee_constant": member["grid_fee_constant"],
            "taxes": member["taxes"],
            "fixed_fee": member["fixed_fee"],
            "marketplace_fee": member["marketplace_fee"],
            "coefficient_percent": member["coefficient_percent"],
            "children": []
        }


def parse_community_datasheet(filename):
    """Parse the content of the community datasheet and return a JSON representation."""
    parser = CommunityDatasheetParser(filename)
    print(json.dumps(parser.parse(), indent=4))


if __name__ == "__main__":
    parse_community_datasheet("./Community_DataSheet_v3.xlsx")
