"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

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
from typing import Dict
from datetime import timedelta
from pendulum import duration, Duration

from gsy_framework.constants_limits import ConstSettings, GlobalConfig, PercentageRangeLimit
from gsy_framework.exceptions import GSySettingsException


def validate_global_settings(settings: Dict) -> None:
    """Validate global config settings of a simulation.

    Raises:
        D3ASettingsException
    """
    slot_length = (settings["slot_length"]
                   if "slot_length" in settings else GlobalConfig.slot_length)
    tick_length = (settings["tick_length"]
                   if "tick_length" in settings else GlobalConfig.tick_length)

    # converting into duration
    if not isinstance(tick_length, Duration):
        tick_length = (duration(seconds=tick_length.seconds)
                       if isinstance(tick_length, timedelta) else duration(seconds=tick_length))
    if not isinstance(slot_length, Duration):
        slot_length = (duration(minutes=slot_length.seconds / 60)
                       if isinstance(slot_length, timedelta) else duration(minutes=slot_length))

    if "tick_length" in settings:
        min_tick_length, max_tick_length = calc_min_max_tick_length(slot_length)
        if not min_tick_length <= tick_length <= max_tick_length:
            raise GSySettingsException("Invalid tick_length "
                                       f"({tick_length.in_seconds()} sec, limits: "
                                       f"[{min_tick_length.in_seconds()} sec, "
                                       f"{max_tick_length.in_seconds()} sec])")
    if "slot_length" in settings:
        min_slot_length, max_slot_length = calc_min_max_slot_length(tick_length)
        if not min_slot_length <= slot_length <= max_slot_length:
            raise GSySettingsException("Invalid slot_length "
                                       f"({slot_length.in_minutes()} min, limits: "
                                       f"[{min_slot_length.in_minutes()} min, "
                                       f"{max_slot_length.in_minutes()} min])")
    if ("cloud_coverage" in settings and
            not (ConstSettings.PVSettings.CLOUD_COVERAGE_LIMIT[0]
                 <= settings["cloud_coverage"] <=
                 ConstSettings.PVSettings.CLOUD_COVERAGE_LIMIT[1])):
        raise GSySettingsException("Invalid cloud coverage value "
                                   f"({settings['cloud_coverage']}).")
    if ("spot_market_type" in settings
            and not ConstSettings.MASettings.MARKET_TYPE_LIMIT[0]
            <= settings["spot_market_type"]
            <= ConstSettings.MASettings.MARKET_TYPE_LIMIT[1]):
        raise GSySettingsException(f"Invalid value ({settings['spot_market_type']}) "
                                   "for spot market type.")

    if "sim_duration" in settings and not slot_length <= settings["sim_duration"]:
        raise GSySettingsException("Invalid simulation duration "
                                   f"(lower than slot length of {slot_length.minutes} min")

    if ("capacity_kW" in settings and not
            ConstSettings.PVSettings.CAPACITY_KW_LIMIT.min
            <= settings["capacity_kW"]
            <= ConstSettings.PVSettings.CAPACITY_KW_LIMIT.max):
        raise GSySettingsException("Invalid value for capacity_kW "
                                   f"({settings['capacity_kW']}).")

    if ("grid_fee_type" in settings and
            int(settings["grid_fee_type"]) not in ConstSettings.MASettings.VALID_FEE_TYPES):
        raise GSySettingsException("Invalid value for grid_fee_type "
                                   f"({settings['grid_fee_type']}).")

    if ("relative_std_from_forecast_percent" in settings and not
            PercentageRangeLimit.min
            <= settings["relative_std_from_forecast_percent"]
            <= PercentageRangeLimit.max):
        raise GSySettingsException("Invalid value for relative_std_from_forecast_percent "
                                   f"({settings['relative_std_from_forecast_percent']}).")

    if ("bid_offer_match_algo" in settings
            and not ConstSettings.MASettings.BID_OFFER_MATCH_TYPE_LIMIT[0]
            <= settings["bid_offer_match_algo"]
            <= ConstSettings.MASettings.BID_OFFER_MATCH_TYPE_LIMIT[1]):
        raise GSySettingsException(f"Invalid value ({settings['bid_offer_match_algo']}) "
                                   "for bid offer match algo.")


def calc_min_max_tick_length(slot_length):
    return (duration(seconds=ConstSettings.GeneralSettings.MIN_TICK_LENGTH_S),
            slot_length / ConstSettings.GeneralSettings.MIN_NUM_TICKS)


def calc_min_max_slot_length(tick_length):
    return (max(tick_length * ConstSettings.GeneralSettings.MIN_NUM_TICKS,
            duration(minutes=ConstSettings.GeneralSettings.MIN_SLOT_LENGTH_M)),
            duration(minutes=ConstSettings.GeneralSettings.MAX_SLOT_LENGTH_M))
