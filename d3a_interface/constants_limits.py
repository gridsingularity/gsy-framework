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

import sys
from collections import namedtuple
from datetime import date, datetime

from pendulum import duration, instance

from d3a_interface.enums import BidOfferMatchAlgoEnum, SpotMarketTypeEnum

RangeLimit = namedtuple('RangeLimit', ('min', 'max'))
RateRange = namedtuple('RateRange', ('initial', 'final'))
PercentageRangeLimit = RangeLimit(0, 100)


class ConstSettings:
    class GeneralSettings:
        # Max energy price (market maker rate) in ct / kWh
        DEFAULT_MARKET_MAKER_RATE = 30  # 0.3 Eur
        # interval between offer/bid postings
        DEFAULT_UPDATE_INTERVAL = 1  # in minutes
        MIN_UPDATE_INTERVAL = 1  # in minutes
        # Number of times Market clearing rate has to be calculated per slot
        MARKET_CLEARING_FREQUENCY_PER_SLOT = 3
        # Flag to enable supply/demand backend plots
        EXPORT_SUPPLY_DEMAND_PLOTS = True
        ENERGY_RATE_DECREASE_PER_UPDATE = 1  # rate decrease in cents_per_update
        SETUP_FILE_PATH = None  # Default path of the available setup files
        EXPORT_DEVICE_PLOTS = True
        EXPORT_ENERGY_TRADE_PROFILE_HR = False
        EXPORT_OFFER_BID_TRADE_HR = False
        # Boolean flag which forces d3a to run in real-time
        RUN_REAL_TIME = False
        # Boolean flag which forces d3a to dispatch events via redis channels
        EVENT_DISPATCHING_VIA_REDIS = False
        RATE_CHANGE_PER_UPDATE_LIMIT = RangeLimit(0, 1000)
        ENERGY_PROFILE_LIMIT = RangeLimit(0, sys.maxsize)

        MIN_NUM_TICKS = 10
        MIN_SLOT_LENGTH_M = 2
        MAX_SLOT_LENGTH_M = 60
        MIN_TICK_LENGTH_S = 1

        REDIS_PUBLISH_FULL_RESULTS = False

    class SettlementMarketSettings:
        MAX_AGE_SETTLEMENT_MARKET_HOURS = 1
        ENABLE_SETTLEMENT_MARKETS = False
        RELATIVE_STD_FROM_FORECAST_FLOAT = 10.0

    class AreaSettings:
        PERCENTAGE_FEE_LIMIT = RangeLimit(0, 100)
        CONSTANT_FEE_LIMIT = RangeLimit(0, sys.maxsize)

    class CommercialProducerSettings:
        ENERGY_RATE_LIMIT = RangeLimit(0, 10000)
        MAX_POWER_KW_LIMIT = RangeLimit(0, 10000000)

    class StorageSettings:
        # least possible state of charge
        MIN_SOC_LIMIT = RangeLimit(0, 99)
        # possible range of state of charge
        INITIAL_CHARGE_LIMIT = RangeLimit(0, 100)

        # Max battery capacity in kWh.
        CAPACITY = 1.2
        CAPACITY_LIMIT = RangeLimit(0.0001, 2000000)
        # Maximum battery power for supply/demand, in Watts.
        MAX_ABS_POWER = 5
        MAX_ABS_POWER_RANGE = RateRange(0.0001, 2000000)
        # Energy buy-limit, storage never buys outside this limit.
        # Unit is ct/kWh.
        BUYING_RATE_RANGE = RateRange(0, 24.9)
        INITIAL_BUYING_RATE_LIMIT = RangeLimit(0, 10000)
        FINAL_BUYING_RATE_LIMIT = RangeLimit(0, 10000)
        # Energy sell-limit, storage never sell outside this limit.
        # Unit is ct/kWh.
        SELLING_RATE_RANGE = RateRange(30, 25)
        INITIAL_SELLING_RATE_LIMIT = RangeLimit(0, 10000)
        FINAL_SELLING_RATE_LIMIT = RangeLimit(0, 10000)
        # Min allowed battery SOC, range is [0, 100] %.
        MIN_ALLOWED_SOC = 10
        # Controls whether energy is sold only on the most expensive market, default is
        # to sell to all markets
        SELL_ON_MOST_EXPENSIVE_MARKET = False

        # Controls the energy loss of the storage over time#
        # LOSS_FUNCTION = 1 ==> relative loss
        # LOSS_FUNCTION = 2 ==> absolute loss
        LOSS_FUNCTION = 1
        LOSS_FUNCTION_LIMIT = RangeLimit(1, 2)
        LOSS_PER_HOUR = 0
        LOSS_PER_HOUR_ABSOLUTE_LIMIT = RangeLimit(0, 10000)
        LOSS_PER_HOUR_RELATIVE_LIMIT = RangeLimit(0, 1)

    class LoadSettings:
        AVG_POWER_LIMIT = RangeLimit(0, sys.maxsize)
        HOURS_LIMIT = RangeLimit(0, 24)
        # Min load energy rate, in ct/kWh
        BUYING_RATE_RANGE = RateRange(0, 35)
        INITIAL_BUYING_RATE_LIMIT = RangeLimit(0, 10000)
        # Max load energy rate, in ct/kWh
        FINAL_BUYING_RATE_LIMIT = RangeLimit(0, 10000)
        LOAD_PENALTY_RATE = 29.2

    class PVSettings:
        DEFAULT_PANEL_COUNT = 1
        PANEL_COUNT_LIMIT = RangeLimit(1, 10000)
        FINAL_SELLING_RATE_LIMIT = RangeLimit(0, 10000)
        INITIAL_SELLING_RATE_LIMIT = RangeLimit(0, 10000)
        CAPACITY_KW_LIMIT = RangeLimit(0, sys.maxsize)
        MAX_PANEL_OUTPUT_W_LIMIT = RangeLimit(0, sys.maxsize)  # needed for backward compatibility
        SELLING_RATE_RANGE = RateRange(30, 0)
        # Applies to the predefined PV strategy, where a PV profile is selected out of 3 predefined
        # ones. Available values 0: sunny, 1: partial cloudy, 2: cloudy, 3: Gaussian
        DEFAULT_POWER_PROFILE = 0
        CLOUD_COVERAGE_LIMIT = RangeLimit(0, 4)
        # Power rating for PVs (Gaussian and Predefined)
        DEFAULT_CAPACITY_KW = 5
        MAX_PANEL_OUTPUT_W = 160  # needed for backward compatibility
        PV_PENALTY_RATE = 0

    class SmartMeterSettings:
        # Production constants
        SELLING_RATE_RANGE = RateRange(30, 0)
        INITIAL_SELLING_RATE_LIMIT = RangeLimit(0, 10000)
        FINAL_SELLING_RATE_LIMIT = RangeLimit(0, 10000)
        # Consumption constants
        BUYING_RATE_RANGE = RateRange(0, 35)
        INITIAL_BUYING_RATE_LIMIT = RangeLimit(0, 10000)
        FINAL_BUYING_RATE_LIMIT = RangeLimit(0, 10000)

    class WindSettings:
        # This price should be just above the marginal costs for a Wind Power Plant - unit is cent
        FINAL_SELLING_RATE = 0
        MAX_WIND_TURBINE_OUTPUT_W = 160

    class IAASettings:
        # Grid fee type:
        # Option 1: constant grid fee
        # Option 2: percentage grid fee
        GRID_FEE_TYPE = 1
        VALID_FEE_TYPES = [1, 2]
        # Market type option
        MARKET_TYPE = SpotMarketTypeEnum.ONE_SIDED.value
        MARKET_TYPE_LIMIT = RangeLimit(1, 2)

        BID_OFFER_MATCH_TYPE = BidOfferMatchAlgoEnum.PAY_AS_BID.value
        BID_OFFER_MATCH_TYPE_LIMIT = RangeLimit(1, 3)

        # Pay as clear offer and bid rate/energy aggregation algorithm
        # Default value 1 stands for line sweep algorithm
        # Value 2 stands for integer precision/relaxation algorithm
        PAY_AS_CLEAR_AGGREGATION_ALGORITHM = 1

        MIN_OFFER_AGE = 2
        MIN_BID_AGE = 2

        class AlternativePricing:
            # Option 0: D3A_trading
            # Option 1: no scheme (0 cents/kWh)
            # Option 2: feed-in-tariff (FEED_IN_TARIFF_PERCENTAGE / 100 * MMR)
            # Option 3: net-metering (MMR)
            COMPARE_PRICING_SCHEMES = False
            PRICING_SCHEME = 0
            FEED_IN_TARIFF_PERCENTAGE = 50
            ALT_PRICING_MARKET_MAKER_NAME = "AGENT"

    class BlockchainSettings:
        BC_INSTALLED = True
        # Blockchain URL, default is localhost.
        URL = "http://127.0.0.1:8545"
        # Controls whether a local Ganache blockchain will start automatically by D3A.
        START_LOCAL_CHAIN = True
        # Timeout for blockchain operations, in seconds
        TIMEOUT = 30

    class BalancingSettings:
        # Enables/disables balancing market
        ENABLE_BALANCING_MARKET = False
        # Controls the percentage of the energy traded in the spot market that needs to be
        # acquired by the balancing market on each IAA.
        SPOT_TRADE_RATIO = 0.2
        # Controls the percentage of demand that can be offered on the balancing markets
        # by devices that can offer demand. Range between [0, 1]
        OFFER_DEMAND_RATIO = 0.1
        # Controls the percentage of supply that can be offered on the balancing markets
        # by devices that can offer supply. Range between [0, 1]
        OFFER_SUPPLY_RATIO = 0.1
        # Adds flexible load support.
        FLEXIBLE_LOADS_SUPPORT = True


class GlobalConfig:
    # Default simulation settings d3a-web side
    START_DATE = date.today()
    SLOT_LENGTH_M = 15
    TICK_LENGTH_S = 15
    DURATION_D = 1
    MARKET_COUNT = 1
    CLOUD_COVERAGE = ConstSettings.PVSettings.DEFAULT_POWER_PROFILE
    RANDOM_SEED = 0
    MARKET_MAKER_RATE = str(ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE)
    POWER_FLOW = False
    IS_CANARY_NETWORK = False
    FEED_IN_TARIFF = 20

    # Default simulation settings d3a side:
    start_date = instance((datetime.combine(START_DATE, datetime.min.time())))
    sim_duration = duration(days=DURATION_D)
    market_count = MARKET_COUNT
    slot_length = duration(minutes=SLOT_LENGTH_M)
    tick_length = duration(seconds=TICK_LENGTH_S)
    ticks_per_slot = int(slot_length / tick_length)
    total_ticks = int(sim_duration / tick_length)
    cloud_coverage = ConstSettings.PVSettings.DEFAULT_POWER_PROFILE
    market_maker_rate = ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE
    grid_fee_type = ConstSettings.IAASettings.GRID_FEE_TYPE


class HeartBeat:
    CHANNEL_NAME = "d3a-heartbeat"
    RATE = 5  # in secs
    TOLERANCE = 16  # in secs


TIME_FORMAT = "HH:mm"
TIME_FORMAT_SECONDS = "HH:mm:ss"
DATE_FORMAT = "YYYY-MM-DD"
DATE_TIME_FORMAT = f"{DATE_FORMAT}T{TIME_FORMAT}"
DATE_TIME_FORMAT_SECONDS = f"{DATE_FORMAT}T{TIME_FORMAT_SECONDS}"
DATE_TIME_UI_FORMAT = "MMMM DD YYYY, HH:mm [h]"
TIME_ZONE = 'UTC'
CN_PROFILE_EXPANSION_DAYS = 7

JWT_TOKEN_EXPIRY_IN_SECS = 48 * 3600

DEFAULT_PRECISION = 8
FLOATING_POINT_TOLERANCE = 0.00001
