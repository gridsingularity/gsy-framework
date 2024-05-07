from copy import copy
from unittest.mock import Mock

import pytest

from gsy_framework.validators.profile_validator import ProfileValidator
from tests.test_validators.profile_data import (
    START_TIME, END_TIME_1DAY, END_TIME_2DAY, SLOT_LENGTH, ONE_DAY_PROFILE, MULTI_DAY_PROFILE)


class TestProfileValidator:
    # pylint: disable=protected-access

    @staticmethod
    @pytest.mark.parametrize("input_profile, end_time", [
        (ONE_DAY_PROFILE, END_TIME_1DAY),
        (MULTI_DAY_PROFILE, END_TIME_2DAY)])
    def test_profile_validator_succeeds_when_valid_profile_provided(input_profile, end_time):
        ProfileValidator(
            profile=input_profile,
            start_time=START_TIME,
            end_time=end_time,
            slot_length=SLOT_LENGTH).validate()

    @staticmethod
    @pytest.mark.parametrize("input_profile, end_time", [
        (ONE_DAY_PROFILE, END_TIME_1DAY),
        (MULTI_DAY_PROFILE, END_TIME_2DAY)])
    def test_profile_validator_fails_if_start_date_is_not_respected(input_profile, end_time):
        profile = copy(input_profile)
        del profile[next(iter(profile))]
        with pytest.raises(AssertionError):
            ProfileValidator(
                profile=profile,
                start_time=START_TIME,
                end_time=end_time,
                slot_length=SLOT_LENGTH).validate()

    @staticmethod
    @pytest.mark.parametrize("input_profile, end_time", [
        (ONE_DAY_PROFILE, END_TIME_1DAY),
        (MULTI_DAY_PROFILE, END_TIME_2DAY)])
    def test_profile_validator_fails_if_end_time_is_not_respected(input_profile, end_time):
        profile = copy(input_profile)
        del profile[next(reversed(profile))]
        with pytest.raises(AssertionError):
            ProfileValidator(
                profile=profile,
                start_time=START_TIME,
                end_time=end_time,
                slot_length=SLOT_LENGTH).validate()

    @staticmethod
    @pytest.mark.parametrize("input_profile, end_time", [
        (ONE_DAY_PROFILE, END_TIME_1DAY),
        (MULTI_DAY_PROFILE, END_TIME_2DAY)])
    def test_profile_validator_fails_if_slot_length_not_respected(input_profile, end_time):
        profile = copy(input_profile)
        del profile[next(reversed(profile))]
        wrong_time_stamp = START_TIME.add(minutes=SLOT_LENGTH.minutes / 5)
        input_profile[wrong_time_stamp] = 0.1
        with pytest.raises(AssertionError):
            ProfileValidator(
                profile=profile,
                start_time=START_TIME,
                end_time=end_time,
                slot_length=SLOT_LENGTH).validate()

    @staticmethod
    @pytest.mark.parametrize("input_profile, end_time", [
        (ONE_DAY_PROFILE, END_TIME_1DAY),
        (MULTI_DAY_PROFILE, END_TIME_2DAY)])
    def test_profile_validator_fails_if_gap_in_profile(input_profile, end_time):
        profile = copy(input_profile)
        gap_time = START_TIME.add(minutes=SLOT_LENGTH.minutes * 4)
        del profile[gap_time]
        with pytest.raises(AssertionError):
            ProfileValidator(
                profile=profile,
                start_time=START_TIME,
                end_time=end_time,
                slot_length=SLOT_LENGTH).validate()

    @staticmethod
    @pytest.mark.parametrize("input_profile", [ONE_DAY_PROFILE, MULTI_DAY_PROFILE])
    def test_profile_validator_fails_if_gap_in_profile_no_slot_length(input_profile):
        profile = copy(input_profile)
        gap_time = START_TIME.add(minutes=SLOT_LENGTH.minutes * 4)
        del profile[gap_time]
        with pytest.raises(AssertionError):
            ProfileValidator(profile=profile).validate()

    @staticmethod
    def test_profile_validator_returns_early_if_empty_profile():
        validator = ProfileValidator(profile={})
        validator._validate_slot_length = Mock()
        validator._get_and_validate_time_diffs = Mock()
        validator._validate_start_end_date = Mock()
        validator.slot_length = Mock()
        assert validator.validate() is None
        validator._validate_slot_length.assert_not_called()
        validator._get_and_validate_time_diffs.assert_not_called()
        validator._validate_start_end_date.assert_not_called()
