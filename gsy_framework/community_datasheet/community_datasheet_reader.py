"""Module for the reader of the SCM community datasheet."""

import json
import logging
import pathlib
from dataclasses import asdict, dataclass
from itertools import chain
from typing import IO, Dict, Union

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.sheet_parsers import (
    CommunityMembersSheetParser, GeneralSettingsSheetParser, LoadSheetParser, ProfileSheetParser,
    PVSheetParser, StorageSheetParser)

logger = logging.getLogger(__name__)


@dataclass
class CommunityDatasheet:
    """Dataclass for the parsed contents of the Community Datasheet."""

    settings: Dict
    members: Dict
    loads: Dict
    pvs: Dict
    storages: Dict
    profiles: Dict

    def as_json(self) -> str:
        """Return the JSON representation of the datasheet."""
        return json.dumps(asdict(self), indent=4)


class CommunityDatasheetReader:
    """Parser for Community Datasheet files."""

    SHEETNAMES = {"General settings", "Community Members", "Load", "PV", "Storage", "Profiles"}

    @classmethod
    def read(cls, filename: Union[str, pathlib.Path, IO]) -> Dict:
        """Parse the entire datasheet and return its dataclass.

        Args:
            filename: the path to open or a file-like object.
        """
        workbook = cls._load_workbook(filename)

        cls._validate_sheetnames(workbook)
        datasheet = cls._parse_sheets(workbook)
        cls._validate_missing_profiles(datasheet)

        return datasheet

    @staticmethod
    def _load_workbook(filename: Union[str, pathlib.Path, IO]):
        try:
            return load_workbook(filename, read_only=True)
        except InvalidFileException as ex:
            logger.debug("Error while parsing community datasheet: %s", ex)
            raise CommunityDatasheetException(
                "Community Datasheet format not supported. "
                "Please make sure to use a proper Excel .xlsx file.") from ex

    @classmethod
    def _validate_sheetnames(cls, workbook) -> None:
        current_sheetnames = set(workbook.sheetnames)
        if not current_sheetnames == cls.SHEETNAMES:
            raise CommunityDatasheetException(
                f"The datasheet should contain the following sheets: {cls.SHEETNAMES}."
                f"Found: {current_sheetnames}.")

    @staticmethod
    def _parse_sheets(workbook) -> CommunityDatasheet:
        return CommunityDatasheet(
            settings=GeneralSettingsSheetParser(workbook["General settings"]).parse(),
            members=CommunityMembersSheetParser(workbook["Community Members"]).parse(),
            loads=LoadSheetParser(workbook["Load"]).parse(),
            pvs=PVSheetParser(workbook["PV"]).parse(),
            storages=StorageSheetParser(workbook["Storage"]).parse(),
            profiles=ProfileSheetParser(workbook["Profiles"]).parse()
        )

    @staticmethod
    def _validate_missing_profiles(datasheet):
        asset_names = []
        # Storage assets do not define profiles so we don't consider them
        asset_items = [assets.values() for assets in [datasheet.loads, datasheet.pvs]]
        for assets in chain.from_iterable(asset_items):
            asset_names.extend(asset["name"] for asset in assets)

        missing_profiles = [
            asset_name for asset_name in asset_names
            if asset_name not in datasheet.profiles
        ]

        if missing_profiles:
            raise CommunityDatasheetException(
                "Each asset must explicitly define an energy profile in the datasheet. "
                f"The following assets do not define a profile: {missing_profiles}.")
