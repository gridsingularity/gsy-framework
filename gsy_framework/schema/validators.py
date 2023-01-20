import abc
from pathlib import Path

import avro.schema
from avro.errors import AvroTypeException
from avro.io import validate as validate_avro_schema

AVRO_SCHEMAS_PATH = Path(__file__).parent / "avro_schemas"


class BaseSchemaValidator(abc.ABC):
    """Base schema validator class to control inter-service communications."""

    @abc.abstractmethod
    def validate(self, data) -> (bool, str):
        """Validate given data using the defined schema."""


class AVROSchemaValidator(BaseSchemaValidator):
    """Schema validator class that utilizes """
    def __init__(self, schema_name: str):
        with open(AVRO_SCHEMAS_PATH / schema_name) as schema_file:
            self.schema = avro.schema.parse(schema_file.read())

    def validate(self, data):
        try:
            validate_avro_schema(self.schema, data, raise_on_error=True)
            return True, ""
        except AvroTypeException as exc:
            return False, str(exc)


def get_schema_validator(schema_name: str) -> BaseSchemaValidator:
    """Return the appropriate schema validator class based on the schema name."""
    return AVROSchemaValidator(schema_name=schema_name)
