from gsy_framework.schema.validators import get_schema_validator


class TestAggregatorMappingValidator:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self._validator = get_schema_validator("launch_simulation_aggregator_mapping")
        self._data = {
            "c8385b49-d883-4473-afa6-9da7d17dcb79": [
                "d1c2f12e-2ece-4354-a687-724a3f64d2fb",
                "dfe49efc-c270-444a-a33c-3fa09bff3276",
                "14f3e627-3ac5-4c42-9533-1b4d8c0a8653"]
        }

    def test_aggregator_mapping_validator_works(self):
        is_valid, errors = self._validator.validate(self._data, True)
        assert not errors
        assert is_valid is True

    def test_aggregator_mapping_validator_accepts_empty_dict(self):
        is_valid, errors = self._validator.validate({}, True)
        assert not errors
        assert is_valid is True

    def test_aggregator_mapping_validator_rejects_wrong_types(self):
        self._data["c8385b49-d883-4473-afa6-9da7d17dcb79"].append(1)
        is_valid, errors = self._validator.validate(self._data, True)
        assert errors
        assert is_valid is False
