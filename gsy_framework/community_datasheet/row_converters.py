import uuid
from typing import Dict

from gsy_framework.community_datasheet.sheet_headers import (
    LoadSheetHeader, PVSheetHeader, StorageSheetHeader)
from gsy_framework.constants_limits import ConstSettings


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
