import uuid
from datetime import datetime
from typing import Dict

import pendulum

from gsy_framework.community_datasheet.sheet_headers import (
    LoadSheetHeader, PVSheetHeader, StorageSheetHeader)
from gsy_framework.constants_limits import DATE_TIME_FORMAT, ConstSettings


class GeneralSettingsRowConverter:
    """Convert from the excel row to a grid representation of a Load asset."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using just the field name and value.

        The field name is converted to snake case.
        """
        field_name, value = row[0], row[2]  # Each row is a tuple (setting-name, legend, value)
        field_name = field_name.strip().lower().replace(" ", "_")
        if isinstance(value, datetime):
            value = pendulum.instance(value).format(DATE_TIME_FORMAT)

        return {field_name.strip().lower(): value}


class MembersRowConverter:
    """Convert from the excel row to a dictionary representing member information."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """Convert the row using keys that will be added to the grid representation."""
        return {
            "email": row["Email"],
            "zip_code": row["ZIP code"],
            "address": row["Location/Address (optional)"],
            "market_maker_rate": row["Utility price"],
            "feed_in_tariff": row["Feed-in Tariff"],
            "grid_fee_constant": row["Grid fee"],
            "taxes": row["Taxes and surcharges"],
            "fixed_fee": row["Fixed fee"],
            "marketplace_fee": row["Marketplace fee"],
            "coefficient_percent": row["Coefficient"]
        }


class LoadRowConverter:
    """Convert from the excel row to a grid representation of a Load asset."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        # One of the following:
        # ["LoadHoursStrategy", "DefinedLoadStrategy",
        # "LoadHoursExternalStrategy", "LoadProfileExternalStrategy",
        # "LoadForecastExternalStrategy", "Load"]
        return {
            "name": row[LoadSheetHeader.LOAD_NAME],
            "type": "Load",
            "uuid": str(uuid.uuid4())
        }


class PVRowConverter:
    """Convert from the excel row to a grid representation of a PV asset."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
        return {
            "name": row[PVSheetHeader.PV_NAME],
            "type": "PV",
            "uuid": str(uuid.uuid4()),
            "capacity_kW": (
                row[PVSheetHeader.CAPACITY_KW] or ConstSettings.PVSettings.DEFAULT_CAPACITY_KW),
            "tilt": row[PVSheetHeader.TILT],
            "azimuth": row[PVSheetHeader.AZIMUTH]
        }


class StorageRowConverter:
    """Convert from the excel row to a grid representation of a Storage asset."""

    @classmethod
    def convert(cls, row: Dict) -> Dict:
        """
        Convert the row parsed from the Excel file to the asset representation used in scenarios.
        """
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
