from collections import OrderedDict
from datetime import timedelta
from typing import Dict

from pendulum import DateTime, duration

from gsy_framework.utils import convert_str_to_pendulum_in_dict


class ProfileValidator:
    """Validate profiles"""

    def __init__(self, profile: Dict[str, float], start_time: DateTime, end_time: DateTime,
                 slot_length: timedelta):
        assert len(profile) > 0, "profile is empty"
        self.profile = OrderedDict(convert_str_to_pendulum_in_dict(profile))
        self.start_time = start_time
        self.end_time = end_time
        self.slot_length = slot_length

    def validate(self):
        """Validate if profile corresponds to the start_time, end_time and slot_length setting."""
        self._validate_start_end_date()
        self._validate_slot_length()

    @property
    def _profile_start_time(self) -> DateTime:
        return next(iter(self.profile))

    @property
    def _profile_end_time(self) -> DateTime:
        return next(reversed(self.profile))

    def _validate_start_end_date(self):
        assert self._profile_start_time <= self.start_time, (
            f"start_time is not valid {self._profile_start_time}, should be <= {self.start_time}")
        if (self._profile_end_time -
                self._profile_start_time == duration(days=1) - self.slot_length):
            # if the profile is only one day long, it will be copied to other days and
            # consequently, the end_date does not have to be validated
            return
        assert self._profile_end_time >= self.end_time, (
            f"end_time is not valid {self._profile_end_time}, should be >= {self.end_time}")

    def _validate_slot_length(self):
        first_time = self._profile_start_time
        for time_slot in list(self.profile.keys())[1:]:
            assert first_time.add(seconds=int(self.slot_length.total_seconds())) == time_slot, (
                f"Profile timestamp {time_slot} does not follow the slot length "
                f"{self.slot_length.total_seconds() / 60} minutes "
                f"(previous time_slot: {first_time})")
            first_time = time_slot
