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
import pytest
from pendulum import duration
from datetime import timedelta
from gsy_framework.settings_validators import validate_global_settings
from gsy_framework.exceptions import D3ASettingsException
from gsy_framework.constants_limits import ConstSettings, PercentageRangeLimit


class TestValidateGlobalSettings:
    """Test the settings_validators.validate_global_settings function."""

    def test_wrong_tick_and_slot_lengths(self):
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"tick_length": duration(seconds=15),
                 "slot_length":
                     duration(seconds=15) * (ConstSettings.GeneralSettings.MIN_NUM_TICKS - 1)})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"slot_length": duration(
                    minutes=ConstSettings.GeneralSettings.MAX_SLOT_LENGTH_M + 1)}
            )
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"tick_length":
                 duration(minutes=15) / (ConstSettings.GeneralSettings.MIN_NUM_TICKS - 1),
                 "slot_length": duration(minutes=15)})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"tick_length": duration(minutes=16),
                 "slot_length": duration(minutes=15)}
            )
        # test for integer input
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"tick_length": 16 * 60, "slot_length": 15})
        # test for timedelta
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"tick_length": timedelta(minutes=16),
                 "slot_length": timedelta(minutes=15)})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"slot_length": duration(minutes=1)})

        validate_global_settings({"tick_length": duration(seconds=10),
                                  "slot_length": duration(
                                      minutes=ConstSettings.GeneralSettings.MIN_SLOT_LENGTH_M)})

    def test_wrong_sim_duration(self):
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"slot_length": duration(minutes=15),
                 "sim_duration": duration(minutes=14)})

    def test_wrong_spot_market_type(self):
        """Validate that spot_market_type should be within the range limit."""
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"spot_market_type": ConstSettings.IAASettings.MARKET_TYPE_LIMIT.min - 1})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"spot_market_type": ConstSettings.IAASettings.MARKET_TYPE_LIMIT.max + 1})
        validate_global_settings(
            {"spot_market_type": ConstSettings.IAASettings.MARKET_TYPE_LIMIT.max})

    def test_wrong_bid_offer_match_algo(self):
        """Validate that bid_offer_match_algo should be within the range limit."""
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"bid_offer_match_algo":
                 ConstSettings.IAASettings.BID_OFFER_MATCH_TYPE_LIMIT.min - 1})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"bid_offer_match_algo":
                 ConstSettings.IAASettings.BID_OFFER_MATCH_TYPE_LIMIT.max + 1})
        validate_global_settings(
            {"bid_offer_match_algo":
             ConstSettings.IAASettings.BID_OFFER_MATCH_TYPE_LIMIT.max})

    def test_wrong_cloud_coverage(self):
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"cloud_coverage": ConstSettings.PVSettings.CLOUD_COVERAGE_LIMIT.min - 1})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"cloud_coverage": ConstSettings.PVSettings.CLOUD_COVERAGE_LIMIT.max + 1})

    def test_wrong_capacity_kW(self):
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"capacity_kW":
                 ConstSettings.PVSettings.CAPACITY_KW_LIMIT.min - 1})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"capacity_kW":
                 ConstSettings.PVSettings.CAPACITY_KW_LIMIT.min - 1})
        with pytest.raises(D3ASettingsException):
            validate_global_settings(
                {"capacity_kW":
                 ConstSettings.PVSettings.CAPACITY_KW_LIMIT.max + 1})

    def test_wrong_grid_fee_type(self):
        validate_global_settings({"grid_fee_type": 1})
        with pytest.raises(D3ASettingsException):
            validate_global_settings({"grid_fee_type": 0})
        with pytest.raises(D3ASettingsException):
            validate_global_settings({"grid_fee_type": 3})

    def test_std_from_forecast_percent(self):
        validate_global_settings({"relative_std_from_forecast_percent": 50})
        with pytest.raises(D3ASettingsException):
            validate_global_settings({
             "relative_std_from_forecast_percent": PercentageRangeLimit.min - 1
            })
        with pytest.raises(D3ASettingsException):
            validate_global_settings({
             "relative_std_from_forecast_percent": PercentageRangeLimit.max + 1
            })
