import abc
import logging
from pathlib import Path
from typing import Dict

import avro.schema
from avro.errors import AvroTypeException
from avro.io import validate as validate_avro_schema
from avro import io

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


class AVROSimulationSettingsValidator:

    def __init__(self):
        with open(AVRO_SCHEMAS_PATH / "launch_simulation_settings.json") as schema_file:
            self.schema = avro.schema.parse(schema_file.read())

    def validate(self, data: Dict, raise_exception: bool = False) -> (bool, str):
        data["duration"] = data["duration"].total_seconds()
        data["slot_length"] = data["slot_length"].total_seconds()
        data["tick_length"] = data["tick_length"].total_seconds()
        data["slot_length_realtime"] = data["slot_length_realtime"].total_seconds()
        return super().validate(data, raise_exception)

    def validate_and_serialize(self, data: Dict, raise_exception: bool):
        self.validate(data, raise_exception)
        writer = avro.io.DatumWriter(self.schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)


def get_schema_validator(schema_name: str) -> BaseSchemaValidator:
    """Return the appropriate schema validator class based on the schema name."""
    return AVROSchemaValidator(schema_name=schema_name)
