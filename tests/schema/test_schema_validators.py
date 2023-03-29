import pytest

from gsy_framework.schema.validators import (BaseSchemaValidator, SchemaError,
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
        validator = get_schema_validator(schema_name=schema_name)
        assert validator.validate({})[0] is True
        assert validator.validate(None)[0] is False
        try:
            is_valid, _ = validator.validate(None, raise_exception=True)
            # pytest.fail("Schema validator not working correctly.")
            assert not is_valid
        except SchemaError:
            pytest.fail("Remove this when AVROSchemaValidator raises exceptions again.")

    @staticmethod
    def test_configuration_tree_validator_works_correctly():
        validator = get_schema_validator("results_configuration_tree")
        is_valid, _ = validator.validate({
            "name": "grid", "uuid": "", "parent_uuid": "", "type": "Area", "children": [
                {"name": "PV", "uuid": "", "parent_uuid": "", "type": "PV"},
                {"name": "Load", "uuid": "", "parent_uuid": "", "type": "Load"},
                {"name": "Load2", "uuid": "", "parent_uuid": "",
                 "type": "Load", "capacity_kW": 0.2},
            ]
        })
        assert is_valid is True
        is_valid, _ = validator.validate({"name": "Area", "uuid": "", "parent_uuid": ""})
        assert is_valid is True

    @staticmethod
    def test_configuration_tree_validator_fails_with_missing_arguments():
        validator = get_schema_validator("results_configuration_tree")
        is_valid, _ = validator.validate({})
        assert is_valid is False
        is_valid, _ = validator.validate(None)
        assert is_valid is False
        is_valid, _ = validator.validate({"name": "Load", "uuid": "", "type": "Area"})
        assert is_valid is False
        is_valid, _ = validator.validate({"name": "Load", "parent_uuid": "", "type": "Area"})
        assert is_valid is False
        is_valid, _ = validator.validate({"uuid": "", "parent_uuid": "", "type": "Area"})
        assert is_valid is False
        is_valid, _ = validator.validate({
            "name": "grid", "parent_uuid": "", "type": "Area", "children": [
                {"name": "PV", "uuid": "", "type": "PV"},
                {"name": "Load", "uuid": "", "parent_uuid": ""},
            ]
        })
        assert is_valid is False


def test_get_schema_validator():
    validator = get_schema_validator(schema_name="simulation_raw_data")
    assert isinstance(validator, BaseSchemaValidator)
