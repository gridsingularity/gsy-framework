import logging
from datetime import timedelta

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from jsonschema.validators import extend

from gsy_framework.community_datasheet.community_datasheet_reader import CommunityDatasheet
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.community_datasheet.schema import COMMUNITY_DATASHEET_SCHEMA
from gsy_framework.constants_limits import FIELDS_REQUIRED_FOR_REBASE
from gsy_framework.scenario_validators import scenario_validator

logger = logging.getLogger(__name__)


class CommunityDatasheetValidator:
    """Validator for the parsed community datasheet output."""

    def __init__(self):
        # JSON schema doesn't work with datetime or custom objects, so we customise it
        type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
            "custom_timedelta", self._is_timedelta)
        CustomValidator = extend(Draft202012Validator, type_checker=type_checker)
        self._validator = CustomValidator(schema=COMMUNITY_DATASHEET_SCHEMA)

    def validate(self, datasheet: CommunityDatasheet):
        """Validate the JSON output of the datasheet."""
        try:
            self._validator.validate(instance=datasheet.as_dict())
        except ValidationError as ex:
            raise CommunityDatasheetException(ex) from ex

        self._validate_loads(datasheet)
        self._validate_pvs(datasheet)
        self._validate_grid(datasheet.grid)

    @staticmethod
    def _is_timedelta(_checker, instance):
        return isinstance(instance, timedelta)

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

    @staticmethod
    def _validate_grid(grid):
        try:
            scenario_validator(grid)
        except ValidationError as ex:
            message = (
                f"Validation error for the grid in path: {list(ex.absolute_path)}. "
                f"Error: {ex.message}")
            logger.exception(message)
            raise CommunityDatasheetException(message) from ex
