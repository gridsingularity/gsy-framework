"""Module defining headers of the community datasheet excel files."""

from enum import Enum


class LoadSheetHeader(str, Enum):
    """Class defining the header columns of the Load Sheet."""

    MEMBER_NAME = "Member_name"
    LOAD_NAME = "Load_name"
    DATASTREAM_ID = "Datastream_ID"

    @classmethod
    def values(cls):
        """Return all available values of the header."""
        return tuple(item.value for item in cls)


class PVSheetHeader(str, Enum):
    """Class defining the header columns of the PV Sheet."""

    MEMBER_NAME = "Member_name"
    PV_NAME = "PV_name"
    CAPACITY_KW = "Capacity [kW]"
    TILT = "Tilt [°]"
    AZIMUTH = "Azimuth [°]"
    DATASTREAM_ID = "Datastream_ID"

    @classmethod
    def values(cls):
        """Return all available values of the header."""
        return tuple(item.value for item in cls)


class StorageSheetHeader(str, Enum):
    """Class defining the header columns of the Storage Sheet."""

    MEMBER_NAME = "Member_name"
    BATTERY_NAME = "Battery_name"
    DATASTREAM_ID = "Datastream_ID"

    @classmethod
    def values(cls):
        """Return all available values of the header."""
        return tuple(item.value for item in cls)


class CommunityMembersSheetHeader(str, Enum):
    """Class defining the header columns of the Storage Sheet."""

    MEMBER_NAME = "Member list name"
    EMAIL = "Email"
    ZIP = "ZIP code"
    LOCATION = "Location/Address (optional)"
    UTILITY_PRICE = "Utility price"
    FEED_IN_TARIFF = "Feed-in Tariff"
    GRID_FEE = "Grid fee"
    COEFFICIENT = "Coefficient"

    @classmethod
    def values(cls):
        """Return all available values of the header."""
        return tuple(item.value for item in cls)


class CommunityMembersSheetHeaderOptional(str, Enum):
    """Class defining the header columns of the Storage Sheet."""

    TAXES = "Taxes and surcharges"
    FIXED_FEE = "Fixed fee"
    MARKETPLACE_FEE = "Marketplace fee"
    SERVICE_FEE = "Service fee"
    ASSISTANCE_FEE = "Assistance fee"

    @classmethod
    def values(cls):
        """Return all available values of the header."""
        return tuple(item.value for item in cls)
