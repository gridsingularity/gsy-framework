"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from d3a_interface.constants_limits import ConstSettings, GlobalConfig
from d3a_interface.exceptions import SettingsException
from pendulum import duration, Duration
from datetime import timedelta


def validate_global_settings(settings_dict):
    slot_length = settings_dict["slot_length"] \
        if "slot_length" in settings_dict else GlobalConfig.slot_length
    tick_length = settings_dict["tick_length"] \
        if "tick_length" in settings_dict else GlobalConfig.tick_length

    # converting into duration
    if not isinstance(tick_length, Duration):
        tick_length = duration(seconds=tick_length.seconds) \
            if isinstance(tick_length, timedelta) else duration(seconds=tick_length)
    if not isinstance(slot_length, Duration):
        slot_length = duration(minutes=slot_length.seconds / 60) \
            if isinstance(slot_length, timedelta) else duration(minutes=slot_length)

    if "tick_length" in settings_dict:
        min_tick_length, max_tick_length = calc_min_max_tick_length(slot_length)
        if not min_tick_length <= tick_length <= max_tick_length:
            raise SettingsException(f'Invalid tick_length '
                                    f'({tick_length.in_seconds()} sec, limits: '
                                    f'[{min_tick_length.in_seconds()} sec, '
                                    f'{max_tick_length.in_seconds()} sec])')
    if "slot_length" in settings_dict:
        min_slot_length, max_slot_length = calc_min_max_slot_length(tick_length)
        if not min_slot_length <= slot_length <= max_slot_length:
            raise SettingsException(f'Invalid slot_length '
                                    f'({slot_length.in_minutes()} min, limits: '
                                    f'[{min_slot_length.in_minutes()} min, '
                                    f'{max_slot_length.in_minutes()} min])')
    if "cloud_coverage" in settings_dict and \
        not (ConstSettings.PVSettings.CLOUD_COVERAGE_RANGE[0]
             <= settings_dict["cloud_coverage"] <=
             ConstSettings.PVSettings.CLOUD_COVERAGE_RANGE[1]):
        raise SettingsException(f'Invalid cloud coverage value '
                                f'({settings_dict["cloud_coverage"]}).')
    if "spot_market_type" in settings_dict and \
            not ConstSettings.IAASettings.MARKET_TYPE_RANGE[0] \
            <= settings_dict["spot_market_type"] <= \
            ConstSettings.IAASettings.MARKET_TYPE_RANGE[1]:
        raise SettingsException(f'Invalid value ({settings_dict["spot_market_type"]}) '
                                f'for spot market type.')
    if "sim_duration" in settings_dict and not slot_length <= settings_dict["sim_duration"]:
        raise SettingsException(f"Invalid simulation duration "
                                f"(lower than slot length of {slot_length.minutes} min")
    if "iaa_fee" in settings_dict and not \
            ConstSettings.IAASettings.FEE_PERCENTAGE_RANGE[0] \
            <= settings_dict["iaa_fee"] <= \
            ConstSettings.IAASettings.FEE_PERCENTAGE_RANGE[1]:
        raise SettingsException(f'Invalid iaa_fee percentage ({settings_dict["iaa_fee"]}).')
    if "iaa_fee_const" in settings_dict and not \
            ConstSettings.IAASettings.FEE_CONSTANT_RANGE[0] \
            <= settings_dict["iaa_fee_const"] <= \
            ConstSettings.IAASettings.FEE_CONSTANT_RANGE[1]:
        raise SettingsException(f'Invalid constant iaa_fee ({settings_dict["iaa_fee_const"]}).')
    if "market_count" in settings_dict and not 1 <= settings_dict["market_count"]:
        raise SettingsException("Market count must be greater than 0.")
    if "max_panel_power_W" in settings_dict and not \
            ConstSettings.PVSettings.MAX_PANEL_OUTPUT_W_RANGE[0] \
            <= settings_dict["max_panel_power_W"] \
            <= ConstSettings.PVSettings.MAX_PANEL_OUTPUT_W_RANGE[1]:
        raise SettingsException(f'Invalid value for max_panel_power_W '
                                f'({settings_dict["max_panel_power_W"]}).')


def calc_min_max_tick_length(slot_length):
    return duration(seconds=ConstSettings.GeneralSettings.MIN_TICK_LENGTH_S), \
           slot_length / ConstSettings.GeneralSettings.MIN_NUM_TICKS


def calc_min_max_slot_length(tick_length):
    return max(tick_length * ConstSettings.GeneralSettings.MIN_NUM_TICKS,
               duration(minutes=ConstSettings.GeneralSettings.MIN_SLOT_LENGTH_M)), \
           duration(minutes=ConstSettings.GeneralSettings.MAX_SLOT_LENGTH_M)
