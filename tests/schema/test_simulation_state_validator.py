import inspect
import json
import os

import tests
from gsy_framework.schema.validators import AVROSchemaSerializer

TEST_PATH = os.path.dirname(inspect.getsourcefile(tests))


class TestSimulationStateValidator:

    @staticmethod
    def test_simulations_state_schema_works():
        data_path = os.path.join(
            TEST_PATH, "schema", "test_data", "simulation_state_test_data.json")
        with open(data_path, "r", encoding="utf-8") as data_file:
            data = json.load(data_file)
        validator = AVROSchemaSerializer("simulation_state")
        is_valid, errors = validator.validate(data, True)
        assert not errors
        assert is_valid is True
