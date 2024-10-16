# pylint: disable=invalid-name
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple, List

import pendulum

from gsy_framework import NULL_VALUES
from gsy_framework.community_datasheet.exceptions import (
    CommunityDatasheetException,
    StringToTimedeltaConversionException,
)
from gsy_framework.community_datasheet.location_converter import (
    LocationConverter,
    LocationConverterException,
)
from gsy_framework.community_datasheet.sheet_headers import (
    LoadSheetHeader,
    PVSheetHeader,
    StorageSheetHeader,
    CommunityMembersSheetHeaderOptional,
)
from gsy_framework.constants_limits import ConstSettings
from gsy_framework.utils import use_default_if_null

logger = logging.getLogger(__name__)


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
                'Please use [h]:mm (e.g. "1h30m").'
            )

        parts = parts.groupdict(default=0)

        return timedelta(hours=int(parts["hours"]), minutes=int(parts["minutes"]))


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
                    f"Field can't be parsed ({field_name}). {ex}"
                ) from ex

        return {field_name.strip().lower(): value}

    @classmethod
    def _validate_row(cls, row: Tuple):
        if row[2] in NULL_VALUES:
            raise CommunityDatasheetException(
                ("Missing value for required field. " f"Row: {row}. Required field: {row[0]}.")
            )


class MembersRowConverter:
    """Convert from the excel row to a dictionary representing member information."""

    OPTIONAL_FIELDS = (
        "Location/Address (optional)",
        CommunityMembersSheetHeaderOptional.CONTRACTED_POWER_FEE,
        CommunityMembersSheetHeaderOptional.CONTRACTED_POWER_CARGO_FEE,
        CommunityMembersSheetHeaderOptional.ENERGY_CARGO_FEE,
        CommunityMembersSheetHeaderOptional.DATASTREAM_ID,
    )

    @classmethod
    def create_member_dict(
        cls,
        email: str,
        member_uuid: str,
        zip_code: str,
        address: str,
        market_maker_rate: float,
        feed_in_tariff: float,
        grid_import_fee_const: float,
        grid_export_fee_const: float,
        taxes_surcharges: float,
        fixed_monthly_fee: float,
        marketplace_monthly_fee: float,
        assistance_monthly_fee: float,
        coefficient_percentage: float,
        geo_tag_location: List = None,
        asset_count: int = 0,
        member_name: str = None,
        contracted_power_monthly_fee: float = 0.0,
        contracted_power_cargo_monthly_fee: float = 0.0,
        energy_cargo_fee: float = 0.0,
        datastream_id: str = None,
    ):
        # pylint: disable=too-many-arguments, too-many-locals
        """Create a community member dict from individual member information."""
        zip_code = cls._parse_zip_code(zip_code)
        if not geo_tag_location:
            geo_tag_location = AssetCoordinatesBuilder().get_member_coordinates(
                {"address": address, "zip_code": zip_code}
            )
        return {
            "email": email,
            "uuid": member_uuid,
            "name": member_name or "",
            "zip_code": zip_code,
            "address": address,
            "market_maker_rate": market_maker_rate,
            "feed_in_tariff": feed_in_tariff,
            "grid_import_fee_const": grid_import_fee_const,
            "grid_export_fee_const": grid_export_fee_const,
            "taxes_surcharges": taxes_surcharges,
            "fixed_monthly_fee": fixed_monthly_fee,
            "marketplace_monthly_fee": marketplace_monthly_fee,
            "assistance_monthly_fee": assistance_monthly_fee,
            "coefficient_percentage": coefficient_percentage,
            "geo_tag_location": geo_tag_location,
            "asset_count": asset_count,
            "contracted_power_monthly_fee": contracted_power_monthly_fee,
            "contracted_power_cargo_monthly_fee": contracted_power_cargo_monthly_fee,
            "energy_cargo_fee": energy_cargo_fee,
            "forecast_stream_id": datastream_id,
        }

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using keys that will be added to the grid representation."""

        cls._validate_row(row)

        fixed_fee = row["Service fee"] if "Service fee" in row else row["Fixed fee"]
        assistance_fee = row["Assistance fee"] if "Assistance fee" in row else 0.0
        contracted_power_fee = row.get("Contracted Power Fee", 0.0)
        contracted_power_cargo_fee = row.get("Contracted Power Cargo Fee", 0.0)
        energy_cargo_fee = row.get("Energy Cargo Fee", 0.0)
        datastream_id = row.get("Datastream ID")
        return cls.create_member_dict(
            row["Email"],
            str(uuid.uuid4()),
            cls._parse_zip_code(row["ZIP code"]),
            row["Location/Address (optional)"],
            row["Utility price"],
            row["Feed-in Tariff"],
            row["Grid import fee"],
            row["Grid export fee"],
            row["Taxes and surcharges"],
            fixed_fee,
            row["Marketplace fee"],
            assistance_fee,
            row["Coefficient"],
            contracted_power_monthly_fee=contracted_power_fee,
            contracted_power_cargo_monthly_fee=contracted_power_cargo_fee,
            energy_cargo_fee=energy_cargo_fee,
            datastream_id=datastream_id,
        )

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
            field
            for field, value in row.items()
            if field not in cls.OPTIONAL_FIELDS and value in NULL_VALUES
        ]

        if missing_fields:
            raise CommunityDatasheetException(
                (
                    "Missing values for required fields. "
                    f"Row: {row}. Required fields: {missing_fields}."
                )
            )


class LoadRowConverter:
    """Convert from the excel row to a grid representation of a Load asset."""

    OPTIONAL_FIELDS = (LoadSheetHeader.DATASTREAM_ID,)

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        cls._validate_row(row)

        return {
            "name": row[LoadSheetHeader.LOAD_NAME],
            "type": "Load",
            "uuid": str(uuid.uuid4()),
            "forecast_stream_id": row.get(LoadSheetHeader.DATASTREAM_ID),
        }

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [
            field
            for field, value in row.items()
            if field not in cls.OPTIONAL_FIELDS and value in NULL_VALUES
        ]

        if missing_fields:
            raise CommunityDatasheetException(
                (
                    "Missing values for required fields. "
                    f"Row: {row}. Required fields: {missing_fields}."
                )
            )


class PVRowConverter:
    """Convert from the excel row to a grid representation of a PV asset."""

    # These fields are optional because they can be ignored if a PV profile is explicitly provided
    OPTIONAL_FIELDS = (
        PVSheetHeader.CAPACITY_KW,
        PVSheetHeader.TILT,
        PVSheetHeader.AZIMUTH,
        PVSheetHeader.DATASTREAM_ID,
    )

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
            "capacity_kW": use_default_if_null(
                row[PVSheetHeader.CAPACITY_KW], ConstSettings.PVSettings.DEFAULT_CAPACITY_KW
            ),
            "tilt": row[PVSheetHeader.TILT],
            "azimuth": row[PVSheetHeader.AZIMUTH],
            "forecast_stream_id": row.get(PVSheetHeader.DATASTREAM_ID),
        }

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [
            field
            for field, value in row.items()
            if field not in cls.OPTIONAL_FIELDS and value in NULL_VALUES
        ]

        if missing_fields:
            raise CommunityDatasheetException(
                (
                    "Missing values for required fields. "
                    f"Row: {row}. Required fields: {missing_fields}."
                )
            )


class StorageRowConverter:
    """Convert from the excel row to a grid representation of a Storage asset."""

    OPTIONAL_FIELDS = (StorageSheetHeader.DATASTREAM_ID,)

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        cls._validate_row(row)

        return {
            "name": row[StorageSheetHeader.BATTERY_NAME],
            "type": "ScmStorage",
            "uuid": str(uuid.uuid4()),
            "forecast_stream_id": row.get(StorageSheetHeader.DATASTREAM_ID),
        }

    @classmethod
    def _validate_row(cls, row: Dict):
        missing_fields = [
            field
            for field, value in row.items()
            if field not in cls.OPTIONAL_FIELDS and value in NULL_VALUES
        ]

        if missing_fields:
            raise CommunityDatasheetException(
                (
                    "Missing values for required fields. "
                    f"Row: {row}. Required fields: {missing_fields}."
                )
            )


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
