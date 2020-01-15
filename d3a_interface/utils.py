from pendulum import DateTime
from d3a.constants import DATE_TIME_UI_FORMAT, DATE_TIME_FORMAT


def convert_datetime_to_str_keys(indict, outdict, ui_format=False):
    """
    Converts all Datetime keys in a dict into strings in DATE_TIME_FORMAT
    """

    for key, value in indict.items():
        if isinstance(key, DateTime):
            if not ui_format:
                outdict[key.format(DATE_TIME_FORMAT)] = indict[key]
            else:
                outdict[key.format(DATE_TIME_UI_FORMAT)] = indict[key]
        else:
            if isinstance(indict[key], dict):
                outdict[key] = {}
                convert_datetime_to_str_keys(indict[key], outdict[key])

    return outdict


def generate_market_slot_list_from_config(sim_duration, start_date, market_count, slot_length):
    """
    Returns a list of all slot times
    """
    return [
        start_date + (slot_length * i) for i in range(
            (sim_duration + (market_count * slot_length)) //
            slot_length - 1)
        if (slot_length * i) <= sim_duration]
