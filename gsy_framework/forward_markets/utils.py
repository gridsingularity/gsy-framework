from pendulum import DateTime, Duration


def create_market_slots(start_time: DateTime, end_time: DateTime, slot_length: Duration) -> list:
    """Return a list of DateTimes respecting the start, end and slot length."""

    timestamps = []
    current = start_time
    while current <= end_time:
        timestamps.append(current)
        current = current + slot_length
    return timestamps
