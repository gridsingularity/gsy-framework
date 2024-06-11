from collections import OrderedDict
from datetime import timedelta
from typing import Dict, Optional

from pendulum import DateTime, duration


class ProfileValidator:
    """Validate profiles"""

    def __init__(
            self, profile: Dict[DateTime, float], start_time: Optional[DateTime] = None,
            end_time: Optional[DateTime] = None, slot_length: Optional[timedelta] = None):

        self.profile = OrderedDict(profile)
        if not self.profile:
            return
        self.start_time = start_time if start_time else self._profile_start_time
        self.end_time = end_time if end_time else self._profile_end_time
        self.slot_length: timedelta = slot_length

    def validate(self):
        """Validate if profile corresponds to the start_time, end_time and slot_length setting."""
        if not self.profile:
            return
        if self.slot_length:
            self._validate_slot_length()
        else:
            self.slot_length = self._get_and_validate_time_diffs()
        self._validate_start_end_date()

    @property
    def _profile_start_time(self) -> DateTime:
        return next(iter(self.profile))

    @property
    def _profile_end_time(self) -> DateTime:
        return next(reversed(self.profile))

    def _validate_start_end_date(self):
        assert self._profile_start_time <= self.start_time, (
            f"Profile start time {self._profile_start_time} is not consistent with the simulation "
            f"start time {self.start_time}.")
        if (self._profile_end_time -
                self._profile_start_time == duration(days=1) - self.slot_length):
            # if the profile is only one day long, it will be copied to other days and
            # consequently, the end_date does not have to be validated
            return
        assert self._profile_end_time >= self.end_time, (
            f"Profile end time {self._profile_end_time} is not consistent with the simulation "
            f"end time {self.end_time}.")

    def _validate_slot_length(self):
        first_time = self._profile_start_time
        for time_slot in list(self.profile.keys())[1:]:
            assert first_time.add(seconds=int(self.slot_length.total_seconds())) == time_slot, (
                f"Profile timestamp {time_slot} does not follow the slot length "
                f"{self.slot_length.total_seconds() / 60} minutes "
                f"(previous time_slot: {first_time})")
            first_time = time_slot

    def _get_and_validate_time_diffs(self) -> timedelta:
        timestamps = list(self.profile.keys())
        time_diffs = {
            (end - start).total_seconds() for start, end in zip(timestamps[:-1], timestamps[1:])}
        assert len(time_diffs) == 1
        return timedelta(seconds=next(iter(time_diffs)))
