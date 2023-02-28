import abc
import logging
from copy import deepcopy
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import Dict

import avro.schema
from avro.errors import AvroException
from avro.errors import AvroTypeException
from avro.io import validate as validate_avro_schema

from gsy_framework.exceptions import GSySerializationException

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
        with open(AVRO_SCHEMAS_PATH / f"{schema_name}.json", encoding="utf-8") as schema_file:
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
    # pylint: disable=no-self-use

    def modify_input(self, data: Dict) -> Dict:
        """Modify the input data dict in order for AVRO to properly serialize it."""
        return data

    def modify_output(self, data: Dict) -> Dict:
        """Modify the output data dict in order for AVRO  to properly deserialize it."""
        return data

    def serialize(self, data: Dict, raise_exception: bool) -> bytes:
        """Validate and serialize dictionary."""
        data = self.modify_input(data)
        is_valid, errors = self.validate(data, raise_exception)
        if not is_valid:
            raise GSySerializationException(f"Failed to serialize data: {errors}")
        writer = avro.io.DatumWriter(self.schema)
        bytes_writer = BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        return bytes_writer.getvalue()

    def deserialize(self, data: bytes) -> Dict:
        """Deserialize and validate dictionary."""
        try:
            reader = avro.io.DatumReader(self.schema)
            bytes_reader = BytesIO(data)
            decoder = avro.io.BinaryDecoder(bytes_reader)
            deserialized_dict = reader.read(decoder)
        except AvroException as ex:
            raise GSySerializationException(f"Failed to deserialize data: {str(ex)}.") from ex
        deserialized_dict = self.modify_output(deserialized_dict)
        return deserialized_dict


class AVROSimulationSettingsSerializer(AVROSchemaSerializer):
    """Serializer class for the simulation settings."""

    def __init__(self):
        super().__init__("launch_simulation_settings")

    def modify_input(self, data: Dict) -> Dict:
        try:
            data["duration"] = int(data["duration"].total_seconds())
            data["slot_length"] = int(data["slot_length"].total_seconds())
            data["tick_length"] = int(data["tick_length"].total_seconds())
            data["slot_length_realtime"] = int(data["slot_length_realtime"].total_seconds())
        except (KeyError, ValueError, TypeError) as ex:
            error_log = (
                "Time related parameters on the settings were not set or incorrectly assigned.")
            logger.error(error_log)
            raise GSySerializationException(error_log) from ex
        return data

    def modify_output(self, data: Dict) -> Dict:
        try:
            data["duration"] = timedelta(seconds=data["duration"])
            data["slot_length"] = timedelta(seconds=data["slot_length"])
            data["tick_length"] = timedelta(seconds=data["tick_length"])
            data["slot_length_realtime"] = timedelta(seconds=data["slot_length_realtime"])
        except (KeyError, ValueError, TypeError) as ex:
            error_log = (
                "Time related parameters on the settings were not set or incorrectly assigned.")
            logger.error(error_log)
            raise GSySerializationException(error_log) from ex
        return data


def get_schema_validator(schema_name: str) -> BaseSchemaValidator:
    """Return the appropriate schema validator class based on the schema name."""
    return AVROSchemaValidator(schema_name=schema_name)


class SimulationLaunchSerializer:
    """Responsible for (de)serialization and validation of the simulation launch dict."""

    def __init__(self):
        self._scenario_serializer = AVROSchemaSerializer("launch_simulation_scenario")
        self._settings_serializer = AVROSimulationSettingsSerializer()
        self._aggregator_mapping_serializer = AVROSchemaSerializer(
            "launch_simulation_aggregator_mapping")

    def validate(self, data: Dict) -> bool:
        """
        Validate a simulation launch dict. Returns True if valid dict, False for invalid, and
        raises exceptions in case the input data do not adhere to the modify_input requirements.
        """
        data_to_validate = deepcopy(data)
        is_valid, _ = self._scenario_serializer.validate(data_to_validate["scenario"], True)
        if not is_valid:
            return False
        data_to_validate["settings"] = self._settings_serializer.modify_input(
            data_to_validate["settings"])
        is_valid, _ = self._settings_serializer.validate(data_to_validate["settings"], True)
        if not is_valid:
            return False
        is_valid, _ = self._aggregator_mapping_serializer.validate(
            data_to_validate["aggregator_device_mapping"], True)
        if not is_valid:
            return False
        return True

    def serialize(self, data: Dict) -> Dict:
        """
        Serialize a simulation launch dict. The output is a dict with the individual values
        being compressed bytestrings.
        """
        data["scenario"] = self._scenario_serializer.serialize(data["scenario"], True)
        data["settings"] = self._settings_serializer.serialize(data["settings"], True)
        data["aggregator_device_mapping"] = self._aggregator_mapping_serializer.serialize(
            data["aggregator_device_mapping"], True)
        return data

    def deserialize(self, data: Dict) -> Dict:
        """
        Deserialize a simulation launch dict. The input is a dict with bytestring values, and the
        output is the deserialized dict.
        """
        data["scenario"] = self._scenario_serializer.deserialize(data["scenario"])
        data["settings"] = self._settings_serializer.deserialize(data["settings"])
        data["aggregator_device_mapping"] = self._aggregator_mapping_serializer.deserialize(
            data["aggregator_device_mapping"])
        return data
