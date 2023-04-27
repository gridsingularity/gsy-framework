from copy import copy

import pytest

from gsy_framework.utils import format_datetime
from gsy_framework.validators.profile_validator import ProfileValidator
from tests.test_validators.profile_data import (
    START_TIME, END_TIME_1DAY, END_TIME_2DAY, SLOT_LENGTH, ONE_DAY_PROFILE, MULTI_DAY_PROFILE)


class TestProfileValidator:

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
        print(profile)
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
        wrong_time_stamp = format_datetime(START_TIME.add(minutes=SLOT_LENGTH.minutes / 5))
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
        gap_time = format_datetime(START_TIME.add(minutes=SLOT_LENGTH.minutes * 4))
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
        gap_time = format_datetime(START_TIME.add(minutes=SLOT_LENGTH.minutes * 4))
        del profile[gap_time]
        with pytest.raises(AssertionError):
            ProfileValidator(profile=profile).validate()
