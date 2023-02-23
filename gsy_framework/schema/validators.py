import abc
import logging
from pathlib import Path
from typing import Dict, Optional

import avro.schema
from avro.errors import AvroTypeException
from avro.io import validate as validate_avro_schema
from io import BytesIO

from gsy_framework.exceptions import GSySettingsException, GSyException

logger = logging.getLogger()

AVRO_SCHEMAS_PATH = Path(__file__).parent / "avro_schemas"


class SchemaError(Exception):
    """Exception class to be used by all defined schema validators."""
    def __init__(self, message: str):
        super().__init__(self)
        self.message = message

    def __str__(self):
        return self.message


class BaseSchemaValidator(abc.ABC):
    """Base schema validator class to control inter-service communications."""

    @abc.abstractmethod
    def validate(self, data, raise_exception: bool = False) -> (bool, str):
        """Validate given data using the defined schema."""


class AVROSchemaValidator(BaseSchemaValidator):
    """Schema validator class that utilizes """
    def __init__(self, schema_name: str):
        with open(AVRO_SCHEMAS_PATH / f"{schema_name}.json") as schema_file:
            self.schema = avro.schema.parse(schema_file.read())

    def validate(self, data, raise_exception: bool = False) -> (bool, str):
        try:
            validate_avro_schema(self.schema, data, raise_on_error=True)
            return True, ""
        except AvroTypeException as exc:
            logger.exception("The provided data is invalid for the schema.")
            # TODO: raise the exception when we are sure the schema
            #  matches every corner case of the system + adapt test_schema_validators as well.
            # if raise_exception:
            #     raise SchemaError(
            #         message="The provided data is invalid for the schema.") from exc
            return False, str(exc)


class AVROSchemaSerializer(AVROSchemaValidator):
    """Serializer class that uses AVRO schemas for serializing and deserializing dicts to bytes."""

    def _modify_input(self, data: Dict) -> Dict:
        """Modify the input data dict in order for AVRO to properly serialize it."""
        return data

    def _modify_output(self, data: Dict) -> Dict:
        """Modify the output data dict in order for AVRO  to properly deserialize it."""
        return data

    def validate(self, data: Dict, raise_exception: bool = False) -> (bool, str):
        try:
            data = self._modify_input(data)
        except GSyException as ex:
            return False, str(ex)
        return super().validate(data, raise_exception)

    def serialize(self, data: Dict, raise_exception: bool) -> Optional[bytes]:
        """Validate and serialize dictionary."""
        is_valid, _ = self.validate(data, raise_exception)
        if not is_valid:
            return None
        writer = avro.io.DatumWriter(self.schema)
        bytes_writer = BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        return bytes_writer.getvalue()

    def deserialize(self, data: Dict, raise_exception: bool) -> Optional[bytes]:
        """Deserialize and validate dictionary."""
        is_valid, _ = self.validate(data, raise_exception)
        if not is_valid:
            return None
        writer = avro.io.DatumWriter(self.schema)
        bytes_writer = BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        return bytes_writer.getvalue()


class AVROSimulationSettingsValidator(AVROSchemaSerializer):
    """Serializer class for the simulation settings."""

    def __init__(self):
        super().__init__("launch_simulation_settings")

    def _modify_input(self, data: Dict) -> Dict:
        try:
            data["duration"] = int(data["duration"].total_seconds())
            data["slot_length"] = int(data["slot_length"].total_seconds())
            data["tick_length"] = int(data["tick_length"].total_seconds())
            data["slot_length_realtime"] = int(data["slot_length_realtime"].total_seconds())
        except (KeyError, ValueError, TypeError) as ex:
            error_log = (
                "Time related parameters on the settings were not set or incorrectly assigned.")
            logger.error(error_log)
            raise GSySettingsException(error_log) from ex
        return data


def get_schema_validator(schema_name: str) -> BaseSchemaValidator:
    """Return the appropriate schema validator class based on the schema name."""
    return AVROSchemaValidator(schema_name=schema_name)
