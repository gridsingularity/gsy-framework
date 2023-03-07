import io
from copy import deepcopy
from datetime import timedelta, date
from math import isclose
from typing import Any, Dict

import avro
import pytest

from gsy_framework.exceptions import GSySerializationException
from gsy_framework.schema.validators import get_schema_validator


class TestSimulationSettingsValidator:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self._serializer = get_schema_validator("launch_simulation_settings")
        self._data = {
            "duration": timedelta(days=7),
            "slot_length": timedelta(seconds=900),
            "tick_length": timedelta(seconds=15),
            "market_count": 1,
            "cloud_coverage": 0,
            "pv_user_profile": None,
            "market_maker_rate": 30,
            "slot_length_realtime": timedelta(0),
            "start_date": date(2022, 10, 17),
            "spot_market_type": 2,
            "advanced_settings": None,
            "random_seed": 0,
            "capacity_kW": 5.0,
            "grid_fee_type": 1,
            "external_connection_enabled": False,
            "currency": 0,
            "settlement_market_enabled": False,
            "relative_std_from_forecast_percent": 10.0,
            "bid_offer_match_algo": 1,
            "scm_coefficient_algorithm": 1,
            "type": 0
        }

    @staticmethod
    def _assert_all_settings_values(settings: Dict, compare_timedeltas: bool):
        if compare_timedeltas:
            assert settings["duration"] == timedelta(days=7)
            assert settings["slot_length"] == timedelta(seconds=900)
            assert settings["tick_length"] == timedelta(seconds=15)
            assert settings["slot_length_realtime"] == timedelta(seconds=0)
        else:
            assert isclose(settings["duration"], timedelta(days=7).total_seconds())
            assert isclose(settings["slot_length"], timedelta(seconds=900).total_seconds())
            assert isclose(settings["tick_length"], timedelta(seconds=15).total_seconds())
            assert isclose(settings["slot_length_realtime"], timedelta(seconds=0).total_seconds())
        assert settings["market_count"] == 1
        assert settings["cloud_coverage"] == 0
        assert settings["pv_user_profile"] is None
        assert settings["market_maker_rate"] == 30
        assert settings["start_date"] == date(2022, 10, 17)
        assert settings["spot_market_type"] == 2
        assert settings["advanced_settings"] is None
        assert settings["capacity_kW"] == 5.0
        assert settings["grid_fee_type"] == 1
        assert not settings["external_connection_enabled"]
        assert settings["currency"] == 0
        assert not settings["settlement_market_enabled"]
        assert settings["relative_std_from_forecast_percent"] == 10.0
        assert settings["bid_offer_match_algo"] == 1
        assert settings["scm_coefficient_algorithm"] == 1
        assert settings["type"] == 0

    def test_simulation_settings_validator_works(self):
        serialized_data = self._serializer.serialize(self._data, True)
        bytes_reader = io.BytesIO(serialized_data)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self._serializer.schema)
        settings = reader.read(decoder)
        self._assert_all_settings_values(settings, False)

    @pytest.mark.parametrize("settings_key, settings_value", [
        ("type", "COLLABORATION"),
        ("settlement_market_enabled", 0),
        ("scm_coefficient_algorithm", 1.3),
        ("bid_offer_match_algo", "payasclear"),
        ("relative_std_from_forecast_percent", "ten percent"),
        ("currency", "EUR"),
        ("external_connection_enabled", "yes"),
        ("grid_fee_type", "dynamic"),
    ])
    def test_simulation_settings_validator_rejects_incorrect_values(
            self, settings_key: str, settings_value: Any):
        incorrect_data = deepcopy(self._data)
        incorrect_data[settings_key] = settings_value
        with pytest.raises(GSySerializationException):
            self._serializer.serialize(incorrect_data, True)

    def test_simulation_settings_deserialization_works(self):
        serialized_data = self._serializer.serialize(self._data, True)

        deserialized_data = self._serializer.deserialize(serialized_data)
        self._assert_all_settings_values(deserialized_data, True)
