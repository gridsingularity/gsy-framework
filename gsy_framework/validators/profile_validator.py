from collections import OrderedDict
from datetime import timedelta
from typing import Dict

from pendulum import DateTime, duration

from gsy_framework.utils import convert_str_to_pendulum_in_dict


class ProfileValidator:
    """Validate profiles"""

    @classmethod
    def validate(cls, profile: Dict[str, float], start_time: DateTime, end_time: DateTime,
                 slot_length: timedelta):
        """Validate if profile corresponds to the start_time, end_time and slot_length setting."""
        assert len(profile) > 0, "profile is empty"
        ordered_profile = OrderedDict(convert_str_to_pendulum_in_dict(profile))
        cls._validate_start_end_date(ordered_profile, start_time, end_time, slot_length)
        cls._validate_slot_length(ordered_profile, slot_length)

    @staticmethod
    def _validate_start_end_date(
            profile: Dict[DateTime, float], start_time: DateTime, end_time: DateTime,
            slot_length: timedelta):
        profile_start_time = next(iter(profile))
        profile_end_time = next(reversed(profile))
        assert profile_start_time <= start_time, (
            f"start_time is not valid {profile_start_time}, should be <= {start_time}")
        if profile_end_time - profile_start_time == duration(days=1) - slot_length:
            # if the profile is only one day long, it will be copied to other days and
            # consequently, the end_date does not have to be validated
            return
        assert profile_end_time >= end_time, (
            f"end_time is not valid {profile_end_time}, should be >= {end_time}")

    @staticmethod
    def _validate_slot_length(profile: Dict[DateTime, float], slot_length: timedelta):
        first_time = next(iter(profile))
        for time_slot in list(profile.keys())[1:]:
            assert first_time.add(seconds=int(slot_length.total_seconds())) == time_slot, (
                f"Profile timestamp {time_slot} does not follow the slot length "
                f"{slot_length.total_seconds() / 60} minutes (previous time_slot: {first_time})")
            first_time = time_slot
