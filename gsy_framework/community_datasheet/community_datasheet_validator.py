import logging
from collections import Counter
from datetime import timedelta
from typing import Dict

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from jsonschema.validators import extend
from pendulum.datetime import DateTime

from gsy_framework.community_datasheet.community_datasheet_reader import CommunityDatasheet
from gsy_framework.community_datasheet.exceptions import CommunityDatasheetException
from gsy_framework.constants_limits import FIELDS_REQUIRED_FOR_REBASE
from gsy_framework.scenario_validators import scenario_validator
from gsy_framework.schemas import COMMUNITY_DATASHEET_SCHEMA

logger = logging.getLogger(__name__)


class CommunityDatasheetValidator:
    """Validator for the parsed community datasheet output."""

    def __init__(self):
        self._validator = CommunityDatasheetSchemaValidator()

    def validate(self, datasheet: CommunityDatasheet):
        """Validate the content of the datasheet."""
        self._validate_unique_names(datasheet)
        self._validate_loads(datasheet)
        self._validate_pvs(datasheet)
        self._validate_grid(datasheet.grid)

        try:
            self._validator.validate(instance=datasheet.as_dict())
        except ValidationError as ex:
            raise CommunityDatasheetException(ex) from ex

    @staticmethod
    def _validate_unique_names(datasheet):
        """Validate that there are no duplicate names among all assets and members."""
        all_assets = datasheet.all_assets
        asset_names = Counter(asset["name"] for asset in all_assets)
        duplicates = [name for name, occurrences in asset_names.items() if occurrences > 1]
        if duplicates:
            raise CommunityDatasheetException(
                f"Asset names must be unique. Foudn duplicate names: {duplicates}.")

    @staticmethod
    def _validate_loads(datasheet: CommunityDatasheet):
        missing_profiles = [
            load["name"] for load in datasheet.load_assets
            if load["name"] not in datasheet.profiles
        ]

        if missing_profiles:
            raise CommunityDatasheetException(
                "Each asset must explicitly define an energy profile in the datasheet. "
                f"The following assets do not define a profile: {missing_profiles}.")

    @classmethod
    def _validate_pvs(cls, datasheet: CommunityDatasheet):
        # Each PV without profile must provide the parameters needed to call the Rebase API.
        for pv_asset in datasheet.pv_assets:
            asset_name = pv_asset["name"]
            if asset_name in datasheet.profiles:
                continue

            missing_attributes = [
                field for field in FIELDS_REQUIRED_FOR_REBASE
                if not pv_asset.get(field)
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


class CommunityDatasheetSchemaValidator:
    """JSON schema validator for Community Datasheet.

    JSON schema doesn't support objects by default, so we extend the validator with new checkers.
    """

    def __init__(self):
        # JSON schema doesn't work with datetime or custom objects, so we extend it to do so
        type_checker = Draft202012Validator.TYPE_CHECKER.redefine_many({
            "custom_timedelta": self._is_timedelta,
            "custom_pendulum_datetime": self._is_pendulum_datetime
            })
        CustomValidator = extend(Draft202012Validator, type_checker=type_checker)
        self._schema_validator = CustomValidator(schema=COMMUNITY_DATASHEET_SCHEMA)

    def validate(self, instance: Dict):
        """Validate an instance of community datasheet (in dict format) using JSON schema."""
        self._schema_validator.validate(instance)

    @staticmethod
    def _is_timedelta(_checker, instance):
        return isinstance(instance, timedelta)

    @staticmethod
    def _is_pendulum_datetime(_checker, instance):
        return isinstance(instance, DateTime)
