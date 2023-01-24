import abc
from pathlib import Path

import avro.schema
from avro.errors import AvroTypeException
from avro.io import validate as validate_avro_schema

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
            if raise_exception:
                raise SchemaError(message=f"The provided data is invalid for the schema.") from exc
            return False, str(exc)


def get_schema_validator(schema_name: str) -> BaseSchemaValidator:
    """Return the appropriate schema validator class based on the schema name."""
    return AVROSchemaValidator(schema_name=schema_name)
