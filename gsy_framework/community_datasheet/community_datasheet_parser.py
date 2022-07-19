"""Module for parsing SCM Community Datasheet Excel files."""

import logging
import uuid
from itertools import chain
from typing import Dict

from gsy_framework.community_datasheet.community_datasheet_reader import CommunityDatasheetReader
from gsy_framework.community_datasheet.community_datasheet_validator import (
    CommunityDatasheetValidator)
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.location_converter import (
    LocationConverter, LocationConverterException)
from gsy_framework.constants_limits import ConstSettings, FIELDS_REQUIRED_FOR_REBASE
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

        self._parse_members()
        self._add_coordinates_to_assets()
        self._parse_pvs()
        self._merge_profiles_into_assets()
        self._datasheet.grid = self._create_grid()

        CommunityDatasheetValidator().validate(self._datasheet)

        return self._datasheet

    def _add_coordinates_to_assets(self):
        for member_name, assets in self._datasheet.assets_by_member.items():
            for asset in assets:
                asset["geo_tag_location"] = self._datasheet.members[
                    member_name]["geo_tag_location"]

    def _parse_members(self):
        """Parse the members to add geographical coordinates."""
        coordinates_builder = AssetCoordinatesBuilder()
        for member_details in self._datasheet.members.values():
            coordinates = coordinates_builder.get_member_coordinates(member_details)
            member_details["geo_tag_location"] = coordinates

    def _parse_pvs(self):
        pv_assets = (
            pv_asset
            for member_assets in self._datasheet.pvs.values()
            for pv_asset in member_assets)
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
                    f'Asset type "{asset_type}" is not supported.') from ex
            asset[profile_key] = self._datasheet.profiles[asset_name]

    def _create_grid(self) -> Dict:
        grid = []
        for member_name, assets in self._datasheet.assets_by_member.items():
            home_representation = self._create_home_representation(member_name)
            home_representation["children"] = assets
            grid.append(home_representation)

        return {
            "name": "Grid Market",
            "allow_external_connection": False,
            "uuid": str(uuid.uuid4()),
            "type": "Area",
            "children": [
                {
                    "name": "",
                    "allow_external_connection": False,
                    "uuid": str(uuid.uuid4()),
                    "type": "InfiniteBus",
                    "energy_rate": ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE,
                    "energy_buy_rate": ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE
                },
                {
                    "name": "Community",
                    "allow_external_connection": False,
                    "uuid": str(uuid.uuid4()),
                    "type": "Area",
                    "children": grid
                }
            ]
        }

    def _create_home_representation(self, member_name: str) -> Dict:
        member = self._datasheet.members[member_name]

        return {
            "name": member_name,
            "tags": ["Home"],
            "type": "Area",
            "uuid": str(uuid.uuid4()),
            "geo_tag_location": member["geo_tag_location"],
            "grid_fee_constant": member["grid_fee_constant"],
            "children": [],
            "market_maker_rate": member["market_maker_rate"],
            "feed_in_tariff": member["feed_in_tariff"],
            "taxes_surcharges": member["taxes_surcharges"],
            "fixed_monthly_fee": member["fixed_monthly_fee"],
            "marketplace_monthly_fee": member["marketplace_monthly_fee"],
            "coefficient_percentage": member["coefficient_percentage"],
        }


class AssetCoordinatesBuilder:
    """Build coordinates for assets using the location of their owner (member)."""

    def __init__(self):
        self._location_converter: LocationConverter = self._get_location_converter()

    def get_member_coordinates(self, member_details: Dict):
        """Retrieve the coordinates of the member using their address and postcode."""
        address = member_details["address"] or ""
        zip_code = member_details["zip_code"] or ""
        full_address = f"{address} {zip_code}"
        if not full_address.strip():
            return None

        try:
            return self._location_converter.convert(full_address)
        except LocationConverterException as ex:
            raise CommunityDatasheetException(ex) from ex

    @staticmethod
    def _get_location_converter():
        """Return an instance of a location converter."""
        try:
            return LocationConverter()
        except LocationConverterException as ex:
            logger.error(ex)
            raise ex
