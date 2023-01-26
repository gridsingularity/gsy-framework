import pytest

from gsy_framework.schema.validators import (AVROSchemaValidator,
                                             BaseSchemaValidator, SchemaError,
                                             get_schema_validator)


class TestAVROSchemaValidators:

    @staticmethod
    @pytest.mark.parametrize("schema_name", [
        "scm_simulation_raw_data",
        "simulation_raw_data",
    ])
    def test_v1_validators(schema_name):
        """This test makes sure that all the available schemas are
        compatible to the AVRO format. An exception is raised if the schema is malformed."""
        validator = AVROSchemaValidator(schema_name=schema_name)
        assert validator.validate({})[0] is True
        assert validator.validate(None)[0] is False
        try:
            validator.validate(None, raise_exception=True)
            pytest.fail("Schema validator not working correctly.")
        except SchemaError:
            pass


def test_get_schema_validator():
    validator = get_schema_validator(schema_name="simulation_raw_data")
    assert isinstance(validator, BaseSchemaValidator)
