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
    HeatPumpSheetHeader,
    CommunityMembersSheetHeaderOptional,
    CommunityMembersSheetHeader,
)
from gsy_framework.constants_limits import ConstSettings
from gsy_framework.utils import use_default_if_null, convert_string_to_boolean
from gsy_framework.enums import CoefficientAlgorithm

logger = logging.getLogger(__name__)

# this is in order to expose better naming to the user
ADVANCED_SETTINGS_FIELD_MAPPING = {
    "Coefficient algorithm": "coefficient_algorithm",
    "Grid fees reduction": "grid_fees_reduction",
    "Intracommunity rate": "intracommunity_rate_base_eur",
    "Operational hours of delay": "scm_cn_hours_of_delay",
    "VAT percentage": "vat_percentage",
    "Self consumption type": "self_consumption_type",
    "Enable grid import fee": "enable_grid_import_fee_const",
    "Enable grid export fee": "enable_grid_export_fee_const",
    "Enable taxes surcharges": "enable_taxes_surcharges",
    "Enable electricity tax": "enable_electricity_tax",
    "Enable fixed monthly fee": "enable_fixed_monthly_fee",
    "Enable marketplace monthly fee": "enable_marketplace_monthly_fee",
    "Enable assistance monthly fee": "enable_assistance_monthly_fee",
    "Enable service monthly fee": "enable_service_monthly_fee",
    "Enable contracted power monthly fee": "enable_contracted_power_monthly_fee",
    "Enable contracted power cargo monthly fee": "enable_contracted_power_cargo_monthly_fee",
    "Enable energy cargo fee": "enable_energy_cargo_fee",
}


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

        return {field_name: value}

    @classmethod
    def _validate_row(cls, row: Tuple):
        if row[0] != "Advanced Settings" and row[2] in NULL_VALUES:
            raise CommunityDatasheetException(
                ("Missing value for required field. " f"Row: {row}. Required field: {row[0]}.")
            )


class AdvancedSettingsRowConverter:
    """Convert from the excel row to advanced settings of the community."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using just the field name and value.

        The field name is converted to snake case.
        """
        cls._validate_row(row)

        field_name, value = row[0], row[2]  # Each row is a tuple (setting-name, legend, value)
        field_name = (
            ADVANCED_SETTINGS_FIELD_MAPPING[field_name]
            if field_name in ADVANCED_SETTINGS_FIELD_MAPPING
            else field_name
        )
        if field_name == "coefficient_algorithm":
            return {field_name: cls._get_coefficient_algorithm_enum(value).value}
        if field_name.startswith("enable_"):
            return {field_name: convert_string_to_boolean(value)}
        return {field_name: value}

    @staticmethod
    def _get_coefficient_algorithm_enum(setting: str) -> CoefficientAlgorithm:
        try:
            return [p for p in CoefficientAlgorithm if p.name == setting.upper()][0]
        except IndexError as exc:
            raise CommunityDatasheetException(
                (f"The coefficient type '{setting}' is not supported")
            ) from exc

    @classmethod
    def _validate_row(cls, row: Tuple):
        if row[2] in NULL_VALUES:
            raise CommunityDatasheetException(
                ("Missing value for required field. " f"Row: {row}. Required field: {row[0]}.")
            )


class MembersRowConverter:
    """Convert from the excel row to a dictionary representing member information."""

    OPTIONAL_FIELDS = CommunityMembersSheetHeaderOptional.values()

    @classmethod
    def create_member_dict(
        cls,
        email: str,
        member_uuid: str,
        zip_code: str,
        address: str,
        market_maker_rate: float,
        feed_in_tariff: float,
        coefficient_percentage: float,
        grid_import_fee_const: float,
        grid_export_fee_const: float,
        taxes_surcharges: float,
        electricity_tax: float,
        fixed_monthly_fee: float,
        marketplace_monthly_fee: float,
        assistance_monthly_fee: float,
        service_monthly_fee: float,
        contracted_power_monthly_fee: float,
        contracted_power_cargo_monthly_fee: float,
        energy_cargo_fee: float,
        geo_tag_location: List = None,
        asset_count: int = 0,
        member_name: str = None,
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
            "electricity_tax": electricity_tax,
            "fixed_monthly_fee": fixed_monthly_fee,
            "marketplace_monthly_fee": marketplace_monthly_fee,
            "assistance_monthly_fee": assistance_monthly_fee,
            "service_monthly_fee": service_monthly_fee,
            "coefficient_percentage": coefficient_percentage,
            "geo_tag_location": geo_tag_location,
            "asset_count": asset_count,
            "contracted_power_monthly_fee": contracted_power_monthly_fee,
            "contracted_power_cargo_monthly_fee": contracted_power_cargo_monthly_fee,
            "energy_cargo_fee": energy_cargo_fee,
        }

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using keys that will be added to the grid representation."""

        cls._validate_row(row)

        return cls.create_member_dict(
            email=row[CommunityMembersSheetHeader.EMAIL.value],
            member_uuid=str(uuid.uuid4()),
            zip_code=cls._parse_zip_code(row[CommunityMembersSheetHeader.ZIP.value]),
            address=row[CommunityMembersSheetHeaderOptional.LOCATION.value],
            market_maker_rate=row[CommunityMembersSheetHeader.UTILITY_PRICE.value],
            feed_in_tariff=row[CommunityMembersSheetHeader.FEED_IN_TARIFF.value],
            coefficient_percentage=row[CommunityMembersSheetHeader.COEFFICIENT.value],
            grid_import_fee_const=row.get(
                CommunityMembersSheetHeaderOptional.GRID_IMPORT_FEE.value, 0.0
            ),
            grid_export_fee_const=row.get(
                CommunityMembersSheetHeaderOptional.GRID_EXPORT_FEE.value, 0.0
            ),
            taxes_surcharges=row.get(CommunityMembersSheetHeaderOptional.TAXES.value, 0.0),
            electricity_tax=row.get(
                CommunityMembersSheetHeaderOptional.ELECTRICITY_TAX.value, 0.0
            ),
            fixed_monthly_fee=row.get(CommunityMembersSheetHeaderOptional.FIXED_FEE.value, 0.0),
            marketplace_monthly_fee=row.get(
                CommunityMembersSheetHeaderOptional.MARKETPLACE_FEE.value, 0.0
            ),
            assistance_monthly_fee=row.get(
                CommunityMembersSheetHeaderOptional.ASSISTANCE_FEE.value, 0.0
            ),
            service_monthly_fee=row.get(
                CommunityMembersSheetHeaderOptional.SERVICE_FEE.value, 0.0
            ),
            contracted_power_monthly_fee=row.get(
                CommunityMembersSheetHeaderOptional.CONTRACTED_POWER_FEE.value, 0.0
            ),
            contracted_power_cargo_monthly_fee=row.get(
                CommunityMembersSheetHeaderOptional.CONTRACTED_POWER_CARGO_FEE.value, 0.0
            ),
            energy_cargo_fee=row.get(
                CommunityMembersSheetHeaderOptional.ENERGY_CARGO_FEE.value, 0.0
            ),
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


class AssetsRowConverter:
    """Base class for assets row converters with shared functionality."""

    OPTIONAL_FIELDS: Tuple[str, ...] = ()

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the convert method.")

    @classmethod
    def _validate_row(cls, row: Dict):
        """Validate that required fields are present and not null."""
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


class LoadRowConverter(AssetsRowConverter):
    """Convert from the excel row to a grid representation of a Load asset."""

    OPTIONAL_FIELDS = (LoadSheetHeader.DATASTREAM_ID.value,)

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        cls._validate_row(row)
        return {
            "name": row[LoadSheetHeader.LOAD_NAME.value],
            "type": "Load",
            "uuid": str(uuid.uuid4()),
        }


class PVRowConverter(AssetsRowConverter):
    """Convert from the excel row to a grid representation of a PV asset."""

    OPTIONAL_FIELDS = (
        PVSheetHeader.CAPACITY_KW.value,
        PVSheetHeader.TILT.value,
        PVSheetHeader.AZIMUTH.value,
        PVSheetHeader.DATASTREAM_ID.value,
    )

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        cls._validate_row(row)
        return {
            "name": row[PVSheetHeader.PV_NAME.value],
            "type": "PV",
            "uuid": str(uuid.uuid4()),
            "capacity_kW": use_default_if_null(
                row[PVSheetHeader.CAPACITY_KW.value], ConstSettings.PVSettings.DEFAULT_CAPACITY_KW
            ),
            "tilt": row[PVSheetHeader.TILT.value],
            "azimuth": row[PVSheetHeader.AZIMUTH.value],
        }


class StorageRowConverter(AssetsRowConverter):
    """Convert from the excel row to a grid representation of a Storage asset."""

    OPTIONAL_FIELDS = (StorageSheetHeader.DATASTREAM_ID.value,)

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        cls._validate_row(row)
        return {
            "name": row[StorageSheetHeader.BATTERY_NAME.value],
            "type": "ScmStorage",
            "uuid": str(uuid.uuid4()),
        }


class HeatPumpRowConverter(AssetsRowConverter):
    """Convert from the excel row to a grid representation of a HeatPump asset."""

    OPTIONAL_FIELDS = (HeatPumpSheetHeader.DATASTREAM_ID.value,)

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        cls._validate_row(row)
        return {
            "name": row[HeatPumpSheetHeader.HEATPUMP_NAME.value],
            "type": "ScmHeatPump",
            "uuid": str(uuid.uuid4()),
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
