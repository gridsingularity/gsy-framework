import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple

import pendulum

from gsy_framework.community_datasheet.exceptions import (
    CommunityDatasheetException, StringToTimedeltaConversionException)
from gsy_framework.community_datasheet.sheet_headers import (
    LoadSheetHeader, PVSheetHeader, StorageSheetHeader)
from gsy_framework.constants_limits import ConstSettings

NULL_VALUES = (None, "")


class StringToTimedeltaParser:
    """Class to convert strings to timedelta objects."""

    REGEX = re.compile(r"((?P<hours>\d{1,2}):)?((?P<minutes>\d{1,2}))?")

    @classmethod
    def parse(cls, time_string: str) -> timedelta:
        """Parse a string in the format [h]:mm and return a timedelta object.

        Example:
            >>> StringToTimedeltaParser.parse("24:01")
            datetime.timedelta(days=1, seconds=60)
        """
        parts = cls.REGEX.fullmatch(time_string)
        if not parts:
            raise StringToTimedeltaConversionException(
                f'Value "{time_string}" does not use the supported format. '
                'Please use [h]:mm (e.g. "1h30m").')

        parts = parts.groupdict(default=0)

        return timedelta(
            hours=int(parts["hours"]),
            minutes=int(parts["minutes"]))


class GeneralSettingsRowConverter:
    """Convert from the excel row to settings of the community."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using just the field name and value.

        The field name is converted to snake case.
        """
        cls._validate_row(row)

        field_name, value = row[0], row[2]  # Each row is a tuple (setting-name, legend, value)
        field_name = field_name.strip().lower().replace(" ", "_")
        if field_name in ("start_date", "end_date") and isinstance(value, datetime):
            value = pendulum.instance(value)
        elif field_name == "slot_length":
            try:
                value = StringToTimedeltaParser.parse(value)
            except StringToTimedeltaConversionException as ex:
                raise CommunityDatasheetException(
                    f"Field can't be parsed ({field_name}). {ex}") from ex

        return {field_name.strip().lower(): value}

    @classmethod
    def _validate_row(cls, row: Tuple):
        if row[2] in NULL_VALUES:
            raise CommunityDatasheetException((
                "Missing value for required field. "
                f"Row: {row}. Required field: {row[0]}."))


class MembersRowConverter:
    """Convert from the excel row to a dictionary representing member information."""

    OPTIONAL_FIELDS = ("Location/Address (optional)",)

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using keys that will be added to the grid representation."""

        cls._validate_row(row)

        return {
            "email": row["Email"],
            "zip_code": cls._parse_zip_code(row["ZIP code"]),
            "address": row["Location/Address (optional)"],
            "market_maker_rate": row["Utility price"],
            "feed_in_tariff": row["Feed-in Tariff"],
            "grid_fee_constant": row["Grid fee"],
            "taxes_surcharges": row["Taxes and surcharges"],
            "fixed_monthly_fee": row["Fixed fee"],
            "marketplace_monthly_fee": row["Marketplace fee"],
            "coefficient_percentage": row["Coefficient"]
        }

    @staticmethod
    def _parse_zip_code(zip_code: str) -> str:
        """Force correct conversion to string to avoid strings like '12435.0'"""
        try:
            zip_code = str(int(zip_code))
        except ValueError:
            pass

        return zip_code

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [
            field for field, value in row.items()
            if field not in cls.OPTIONAL_FIELDS and value in NULL_VALUES]

        if missing_fields:
            raise CommunityDatasheetException((
                "Missing values for required fields. "
                f"Row: {row}. Required fields: {missing_fields}."))


class LoadRowConverter:
    """Convert from the excel row to a grid representation of a Load asset."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        cls._validate_row(row)

        return {
            "name": row[LoadSheetHeader.LOAD_NAME],
            "type": "Load",
            "uuid": str(uuid.uuid4())
        }

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [field for field, value in row.items() if value in NULL_VALUES]

        if missing_fields:
            raise CommunityDatasheetException((
                "Missing values for required fields. "
                f"Row: {row}. Required fields: {missing_fields}."))


class PVRowConverter:
    """Convert from the excel row to a grid representation of a PV asset."""

    # These fields are optional because they can be ignored if a PV profile is explicitly provided
    OPTIONAL_FIELDS = ("Capacity [kW]", "Tilt [°]", "Azimuth [°]")

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        cls._validate_row(row)

        return {
            "name": row[PVSheetHeader.PV_NAME],
            "type": "PV",
            "uuid": str(uuid.uuid4()),
            "capacity_kW": (
                row[PVSheetHeader.CAPACITY_KW] or ConstSettings.PVSettings.DEFAULT_CAPACITY_KW),
            "tilt": row[PVSheetHeader.TILT],
            "azimuth": row[PVSheetHeader.AZIMUTH]
        }

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [
            field for field, value in row.items()
            if field not in cls.OPTIONAL_FIELDS and value in NULL_VALUES]

        if missing_fields:
            raise CommunityDatasheetException((
                "Missing values for required fields. "
                f"Row: {row}. Required fields: {missing_fields}."))


class StorageRowConverter:
    """Convert from the excel row to a grid representation of a Storage asset."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        cls._validate_row(row)

        return {
            "name": row[StorageSheetHeader.BATTERY_NAME],
            "type": "Storage",
            "uuid": str(uuid.uuid4()),
            "battery_capacity_kWh": (
                row[StorageSheetHeader.CAPACITY_KWH]
                or ConstSettings.StorageSettings.CAPACITY),
            "min_allowed_soc": (
                row[StorageSheetHeader.MINIMUM_ALLOWED_SOC]
                or ConstSettings.StorageSettings.MIN_ALLOWED_SOC),
            "max_abs_battery_power_kW": (
                row[StorageSheetHeader.MAXIMUM_POWER_KW]
                or ConstSettings.StorageSettings.MAX_ABS_POWER)
        }

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [field for field, value in row.items() if value in NULL_VALUES]

        if missing_fields:
            raise CommunityDatasheetException((
                "Missing values for required fields. "
                f"Row: {row}. Required fields: {missing_fields}."))
