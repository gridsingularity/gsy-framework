from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

import pendulum
from openpyxl.workbook.workbook import Worksheet
from pendulum.datetime import DateTime

from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.row_converters import (
    GeneralSettingsRowConverter, LoadRowConverter, MembersRowConverter, PVRowConverter,
    StorageRowConverter)
from gsy_framework.community_datasheet.sheet_headers import (
    CommunityMembersSheetHeader, LoadSheetHeader, PVSheetHeader, StorageSheetHeader)
from gsy_framework.constants_limits import DATE_TIME_FORMAT


class SheetParserInterface(ABC):
    """Interface for sheet parsers to be used with the Community Datasheet."""

    ROW_CONVERTER_CLASS = None  # Class to convert rows into their representations/dictionaries

    def __init__(self, worksheet: Worksheet) -> Dict:
        self._worksheet = worksheet
        self._rows = None

    @property
    def rows(self):
        """Iterate over the worksheet rows and validate them."""
        if not self._rows:
            self._rows = self._iterate_rows()

        return self._rows

    def _iterate_rows(self):
        for row in self._worksheet.iter_rows(values_only=True):
            if all(cell is None for cell in row):
                continue  # Skip empty rows
            yield row

    def parse(self):
        """Parse a worksheet."""
        self._parse_header()

        return self._parse_rows()

    @abstractmethod
    def _parse_rows(self) -> Dict:
        """Parse all rows of the sheet."""

    @abstractmethod
    def _parse_header(self):
        """Parse the header of the sheet."""

    @classmethod
    def _parse_row(cls, row):
        """Convert the row dictionary to the asset representation used in GSy-E scenarios."""
        if not cls.ROW_CONVERTER_CLASS:
            return row

        return cls.ROW_CONVERTER_CLASS.convert(row)


class GeneralSettingsSheetParser(SheetParserInterface):
    """Parser for the "General settings" sheet of the Community Datasheet."""

    ROW_CONVERTER_CLASS = GeneralSettingsRowConverter

    def _parse_rows(self) -> Dict:
        output = {}
        for row in self.rows:
            try:
                parsed_row = self._parse_row(row)
            except CommunityDatasheetException as ex:
                raise ex

            output.update(parsed_row)

        return output

    def _parse_header(self):
        """This sheet does not have a header."""


class MembersSheetParser(SheetParserInterface):
    """Base class to parse sheets whose rows represent member names."""

    EXPECTED_HEADER: Tuple[str]  # Fields of the header of the sheet
    ROW_CONVERTER_CLASS = MembersRowConverter

    def __init__(self, worksheet: Worksheet) -> Dict:
        super().__init__(worksheet)
        self._header: Optional[Tuple[str]] = None  # Column headers found in the file

    def _parse_rows(self) -> Dict:
        output = {}
        for row in self.rows:
            row_dict = self._row_to_dict(row)
            # The first header is the member name
            member_name = row_dict.pop(self.EXPECTED_HEADER[0])
            if not member_name:
                raise CommunityDatasheetException(
                    f'member name cannot be None. Check sheet "{self._worksheet.title}".')

            member_name = member_name.strip()
            if member_name not in output:
                output[member_name] = []
            parsed_row = self._parse_row(row_dict)
            output[member_name].append(parsed_row)

        return output

    def _row_to_dict(self, row):
        """Convert row to dictionary using the headers as keys."""
        return {field: row[i] for i, field in enumerate(self._header)}

    def _parse_header(self):
        """Use the first row as header and skip it."""
        self._header = tuple(field for field in next(self.rows) if field)
        if not self._header == self.EXPECTED_HEADER:
            raise CommunityDatasheetException(
                f"Could not find expected headers: {self.EXPECTED_HEADER}. Found: {self._header}.")


class CommunityMembersSheetParser(MembersSheetParser):
    """Class to parse the "Community Members" sheets."""

    EXPECTED_HEADER = CommunityMembersSheetHeader.values()

    def _parse_header(self):
        """Check the header and skip it to read the actual content."""
        super()._parse_header()
        # Also skip the second row, as it just contains a legend to explain the row values.
        next(self.rows)

    def _parse_rows(self) -> Dict:
        output = {}
        for row in self.rows:
            row_dict = self._row_to_dict(row)
            # The first header is the member name
            member_name = row_dict.pop(self.EXPECTED_HEADER[0], "").strip()
            if not member_name:
                raise CommunityDatasheetException(
                    f'member name cannot be None. Check sheet "{self._worksheet.title}".')

            if member_name in output:
                raise CommunityDatasheetException(
                    f'Member names must be unique. Found duplicate name: "{member_name}".')

            parsed_row = self._parse_row(row_dict)
            output[member_name] = parsed_row

        return output


class LoadSheetParser(MembersSheetParser):
    """Parser for the "Load" sheet of the Community Datasheet."""

    EXPECTED_HEADER = LoadSheetHeader.values()
    ROW_CONVERTER_CLASS = LoadRowConverter


class PVSheetParser(MembersSheetParser):
    """Parser for the "PV" sheet of the Community Datasheet."""

    EXPECTED_HEADER = PVSheetHeader.values()
    ROW_CONVERTER_CLASS = PVRowConverter


class StorageSheetParser(MembersSheetParser):
    """Parser for the "Storage" sheet of the Community Datasheet."""

    EXPECTED_HEADER = StorageSheetHeader.values()
    ROW_CONVERTER_CLASS = StorageRowConverter


class ProfileSheetParser(MembersSheetParser):
    """Parser for the "Profiles" sheet of the Community Datasheet."""

    EXPECTED_HEADER = ("Datetime", )

    def _parse_rows(self) -> Dict:
        """Parse a worksheet."""
        already_parsed_date_times = []
        output = {}
        for row in self.rows:
            row_dict = self._row_to_dict(row)

            date_time = self._get_profile_datetime(row_dict)
            if date_time in already_parsed_date_times:
                raise CommunityDatasheetException(
                    "Profiles cannot have multiple values for the same datetime."
                    f'Check sheet "{self._worksheet.title}".')

            for asset_name, energy_value in row_dict.items():
                if asset_name not in output:
                    output[asset_name] = {}
                output[asset_name][date_time] = energy_value or 0.0

            already_parsed_date_times.append(date_time)

        return output

    def _parse_header(self):
        """Use (and skip) the first row as header and store the columns as asset names."""
        # NOTE: Add some kind of validation?
        self._header = tuple(field for field in next(self.rows) if field)
        # Also skip the second row, as it just contains a legend to explain the row values.
        next(self.rows)

    def _get_profile_datetime(self, row: Dict) -> DateTime:
        # The first header column is the datetime
        date_time = row.pop(self.EXPECTED_HEADER[0])  # NOTE: modifying the row here is not good
        if not date_time:
            raise CommunityDatasheetException("Datetime cell cannot be empty.")

        date_time = pendulum.instance(date_time)
        date_time_str = date_time.format(DATE_TIME_FORMAT)

        return date_time_str
