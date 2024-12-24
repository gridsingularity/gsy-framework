"""Module defining headers of the community datasheet excel files."""

from enum import Enum


class SheetHeader(str, Enum):
    """Class defining the header columns of the Community Datasheet."""

    @property
    def value(self):
        """Return the string representation of the header."""
        return super().value.lower()

    @classmethod
    def values(cls):
        """Return all available values of the header."""
        return tuple(item.value.lower() for item in cls)


class LoadSheetHeader(SheetHeader):
    """Class defining the header columns of the Load Sheet."""

    MEMBER_NAME = "Member name"
    LOAD_NAME = "Load name"
    DATASTREAM_ID = "Datastream ID"


class PVSheetHeader(SheetHeader):
    """Class defining the header columns of the PV Sheet."""

    MEMBER_NAME = "Member name"
    PV_NAME = "PV name"
    CAPACITY_KW = "Capacity [kW]"
    TILT = "Tilt [°]"
    AZIMUTH = "Azimuth [°]"
    DATASTREAM_ID = "Datastream ID"


class StorageSheetHeader(SheetHeader):
    """Class defining the header columns of the Storage Sheet."""

    MEMBER_NAME = "Member name"
    BATTERY_NAME = "Battery name"
    DATASTREAM_ID = "Datastream ID"


class HeatPumpSheetHeader(SheetHeader):
    """Class defining the header columns of the Storage Sheet."""

    MEMBER_NAME = "Member name"
    HEATPUMP_NAME = "Heat Pump name"
    DATASTREAM_ID = "Datastream ID"


class CommunityMembersSheetHeader(SheetHeader):
    """Class defining the header columns of the Storage Sheet."""

    MEMBER_NAME = "Member name"
    EMAIL = "Email"
    ZIP = "ZIP code"
    UTILITY_PRICE = "Utility price"
    FEED_IN_TARIFF = "Feed-in Tariff"
    COEFFICIENT = "Coefficient"


class CommunityMembersSheetHeaderOptional(SheetHeader):
    """Class defining the header columns of the Storage Sheet."""

    LOCATION = "Location/Address"
    TAXES = "Taxes and surcharges"
    FIXED_FEE = "Fixed fee"
    MARKETPLACE_FEE = "Marketplace fee"
    SERVICE_FEE = "Service fee"
    ASSISTANCE_FEE = "Assistance fee"
    ELECTRICITY_TAX = "Electricity tax"
    GRID_IMPORT_FEE = "Grid import fee"
    GRID_EXPORT_FEE = "Grid export fee"
    CONTRACTED_POWER_FEE = "Contracted Power Fee"
    CONTRACTED_POWER_CARGO_FEE = "Contracted Power Cargo Fee"
    ENERGY_CARGO_FEE = "Energy Cargo Fee"
    DATASTREAM_ID = "Datastream ID"
