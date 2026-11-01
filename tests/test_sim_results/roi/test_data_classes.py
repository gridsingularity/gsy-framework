import json
from copy import deepcopy
from dataclasses import replace
from math import inf, nan

import pytest

from gsy_framework.enums import RandomOrder
from gsy_framework.sim_results.roi.data_classes import PVRoiParameters, RoiBaseline

BASELINE = {
    "fingerprint": {
        "seed": 7,
        "start_date": "2026-06-01 00:00:00+00:00",
        "sim_duration_seconds": 604800.0,
        "slot_length_seconds": 900.0,
        "tick_length_seconds": 15.0,
        "market_type": 1,
        "bid_offer_match_type": 1,
        "grid_fee_type": 1,
        "random_order": "hash",
        "areas": {
            "Community": {
                "type": "Area",
                "grid_fee_constant": 0.0,
                "grid_fee_percentage": None,
                "settings": None,
            },
            "Community/House 1": {
                "type": "LoadHoursStrategy",
                "grid_fee_constant": None,
                "grid_fee_percentage": None,
                "settings": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            },
        },
    },
    "area_bills": {"Community/House 1": 41.2},
    "supplier_rates": {"2026-06-01T00:00": 0.3, "2026-06-01T00:15": 0.31},
}


class TestRoiParameterSet:

    @pytest.mark.parametrize(
        "changes",
        [
            {"horizon_years": 0},
            {"degradation_rate": -0.01},
            {"degradation_rate": 1.0},
            {"discount_rate": -1.0},
            {"retail_escalation_rate": -1.0},
            {"export_escalation_rate": -1.0},
            {"replacement_year": 0},
            {"replacement_year": 26},
        ],
    )
    def test_rejects_parameters_outside_their_domain(self, reference_parameters, changes):
        # Then
        with pytest.raises(ValueError):
            # Given / When
            replace(reference_parameters, **changes)

    @pytest.mark.parametrize(
        "changes",
        [
            {"replacement_year": 25},
            {"degradation_rate": 0.0},
        ],
    )
    def test_accepts_parameters_on_the_edge_of_their_domain(self, reference_parameters, changes):
        # Given / When
        parameters = replace(reference_parameters, **changes)

        # Then
        for name, value in changes.items():
            assert getattr(parameters, name) == value


class TestRoiInputs:

    @pytest.mark.parametrize(
        "changes",
        [
            {"capital_cost_per_kWp": 0.0},
            {"capital_cost_per_kWp": -1300.0},
            {"ownership_share": -0.5},
            {"ownership_share": 1.5},
            {"window_generation_kWh": nan},
            {"avoided_purchase": inf},
            {"annual_generation_kWh": nan},
        ],
    )
    def test_rejects_inputs_outside_their_domain(self, reference_inputs, changes):
        # Then
        with pytest.raises(ValueError):
            # Given / When
            replace(reference_inputs, **changes)


class TestRoiBaseline:

    def test_round_trips_through_json(self):
        # Given
        baseline = RoiBaseline.from_dict(BASELINE)

        # When
        restored = RoiBaseline.from_dict(json.loads(json.dumps(baseline.serializable_dict())))

        # Then
        assert restored == baseline
        assert restored.serializable_dict() == BASELINE
        assert restored.fingerprint.random_order is RandomOrder.HASH

    def test_names_every_invalid_key_by_its_path(self):
        # Given
        baseline = deepcopy(BASELINE)
        del baseline["fingerprint"]["areas"]["Community/House 1"]["settings"]
        baseline["fingerprint"]["seed"] = "7"
        del baseline["supplier_rates"]

        # When
        with pytest.raises(ValueError) as error:
            RoiBaseline.from_dict(baseline)

        # Then
        message = str(error.value)
        assert "fingerprint.areas.Community/House 1.settings is missing" in message
        assert "fingerprint.seed must be int or None, got str" in message
        assert "supplier_rates is missing" in message

    def test_rejects_an_unknown_random_order(self):
        # Given
        baseline = deepcopy(BASELINE)
        baseline["fingerprint"]["random_order"] = "sorted"

        # Then
        with pytest.raises(ValueError, match="fingerprint.random_order must be one of"):
            # When
            RoiBaseline.from_dict(baseline)


class TestPVRoiParameters:

    def test_round_trips_through_json(self):
        # Given
        parameters = PVRoiParameters(1300, 4900, {"House 1": 0.6, "House 2": 0.4})

        # When
        serialized = json.dumps(parameters.serializable_dict())
        restored = PVRoiParameters.from_dict(json.loads(serialized))

        # Then
        assert restored == parameters

    def test_missing_shares_mean_a_single_owner(self):
        # When
        parameters = PVRoiParameters.from_dict({"capital_cost_per_kWp": 1300})

        # Then
        assert parameters.ownership_shares == {}
