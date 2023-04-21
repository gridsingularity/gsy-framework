import pytest

from gsy_framework.utils import format_datetime
from gsy_framework.validators.profile_validator import ProfileValidator
from tests.test_validators.profile_data import (START_DATE, END_DATE, SLOT_LENGTH,
                                                ONE_DAY_PROFILE, MULTI_DAY_PROFILE)


class TestProfileValidator:

    @staticmethod
    @pytest.mark.parametrize("input_profile", [ONE_DAY_PROFILE, MULTI_DAY_PROFILE])
    def test_profile_validator_succeeds_when_valid_profile_provided(input_profile):
        ProfileValidator.validate(
            profile=input_profile,
            start_time=START_DATE,
            end_time=END_DATE,
            slot_length=SLOT_LENGTH)

    @staticmethod
    @pytest.mark.parametrize("input_profile", [ONE_DAY_PROFILE, MULTI_DAY_PROFILE])
    def test_profile_validator_fails_if_start_date_is_not_respected(input_profile):
        del input_profile[next(iter(input_profile))]
        with pytest.raises(AssertionError):
            ProfileValidator.validate(
                profile=input_profile,
                start_time=START_DATE,
                end_time=END_DATE,
                slot_length=SLOT_LENGTH)

    @staticmethod
    @pytest.mark.parametrize("input_profile", [ONE_DAY_PROFILE, MULTI_DAY_PROFILE])
    def test_profile_validator_fails_if_end_date_is_not_respected(input_profile):
        del input_profile[next(reversed(input_profile))]
        with pytest.raises(AssertionError):
            ProfileValidator.validate(
                profile=input_profile,
                start_time=START_DATE,
                end_time=END_DATE,
                slot_length=SLOT_LENGTH)

    @staticmethod
    @pytest.mark.parametrize("input_profile", [ONE_DAY_PROFILE, MULTI_DAY_PROFILE])
    def test_profile_validator_fails_if_slot_length_not_respected(input_profile):
        del input_profile[next(reversed(input_profile))]
        wrong_time_stamp = format_datetime(START_DATE.add(minutes=SLOT_LENGTH.minutes / 5))
        input_profile[wrong_time_stamp] = 0.1
        with pytest.raises(AssertionError):
            ProfileValidator.validate(
                profile=input_profile,
                start_time=START_DATE,
                end_time=END_DATE,
                slot_length=SLOT_LENGTH)

    @staticmethod
    @pytest.mark.parametrize("input_profile", [ONE_DAY_PROFILE, MULTI_DAY_PROFILE])
    def test_profile_validator_fails_if_gap_in_profile(input_profile):
        gap_time = format_datetime(START_DATE.add(minutes=SLOT_LENGTH.minutes * 4))
        del input_profile[gap_time]
        with pytest.raises(AssertionError):
            ProfileValidator.validate(
                profile=input_profile,
                start_time=START_DATE,
                end_time=END_DATE,
                slot_length=SLOT_LENGTH)
