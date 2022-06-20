from jsonschema.validators import validate

from gsy_framework.community_datasheet.community_datasheet_reader import CommunityDatasheet
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.constants_limits import FIELDS_REQUIRED_FOR_REBASE

COMMUNITY_DATASHEET_SCHEMA = {
    "type": "object",
    "properties": {
        "settings": {"$ref": "#/$defs/settings"},
        "grid": {"$ref": "#/$defs/grid"},
    },
    "$defs": {
        "settings": {
            "description": "General settings of the community.",
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "slot_length": {"type": "string"},
                "currency": {
                    "type": "string",
                    "enum": ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CNY", "CHF"]
                },
                "coefficient_type": {
                    "type": "string",
                    "enum": ["constant", "dynamic"]
                },
            },
            "required": ["start_date", "end_date", "slot_length", "currency", "coefficient_type"]
        },
        "grid": {"type": "object"}
    }
}


class CommunityDatasheetValidator:
    """Validator for the parsed community datasheet output."""

    @classmethod
    def validate(cls, datasheet: CommunityDatasheet):
        """Validate the JSON output of the datasheet."""

        validate(instance=datasheet.as_dict(), schema=COMMUNITY_DATASHEET_SCHEMA)
        cls._validate_loads(datasheet)
        cls._validate_pvs(datasheet)

    @staticmethod
    def _validate_loads(datasheet: CommunityDatasheet):
        asset_names = (
            asset["name"] for member_assets in datasheet.loads.values() for asset in member_assets)

        missing_profiles = [
            asset_name for asset_name in asset_names
            if asset_name not in datasheet.profiles
        ]

        if missing_profiles:
            raise CommunityDatasheetException(
                "Each asset must explicitly define an energy profile in the datasheet. "
                f"The following assets do not define a profile: {missing_profiles}.")

    @classmethod
    def _validate_pvs(cls, datasheet: CommunityDatasheet):
        # Each PV without profile must provide the parameters needed to call the Rebase API.
        assets = (asset for member_assets in datasheet.pvs.values() for asset in member_assets)
        for asset in assets:
            asset_name = asset["name"]
            if asset_name in datasheet.profiles:
                continue

            missing_attributes = [
                field for field in FIELDS_REQUIRED_FOR_REBASE
                if not asset.get(field)
            ]

            if missing_attributes:
                raise CommunityDatasheetException(
                    f'The asset "{asset_name}" does not define the following attributes: '
                    f"{missing_attributes}. Either add a profile or provide all the "
                    "missing fields.")
