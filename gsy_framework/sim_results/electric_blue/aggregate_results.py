from collections import defaultdict
from dataclasses import dataclass, fields
from typing import Dict, List

from pendulum import DateTime

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes
from gsy_framework.utils import format_datetime, str_to_pendulum_datetime

# Used by forward markets; the following dictionary defines
# what aggregations are needed for each market type.
MARKET_RESOLUTIONS = {
    AvailableMarketTypes.YEAR_FORWARD: [
        AggregationResolution.RES_1_YEAR,
        AggregationResolution.RES_1_MONTH,
        AggregationResolution.RES_1_WEEK,
        AggregationResolution.RES_1_HOUR,
        AggregationResolution.RES_15_MINUTES
    ],
    AvailableMarketTypes.MONTH_FORWARD: [
        AggregationResolution.RES_1_MONTH,
        AggregationResolution.RES_1_WEEK,
        AggregationResolution.RES_1_HOUR,
        AggregationResolution.RES_15_MINUTES
    ],
    AvailableMarketTypes.WEEK_FORWARD: [
        AggregationResolution.RES_1_WEEK,
        AggregationResolution.RES_1_HOUR,
        AggregationResolution.RES_15_MINUTES
    ],
    AvailableMarketTypes.DAY_FORWARD: [
        AggregationResolution.RES_1_HOUR,
        AggregationResolution.RES_15_MINUTES
    ],
    AvailableMarketTypes.INTRADAY: [
        AggregationResolution.RES_15_MINUTES
    ]
}


@dataclass
class ForwardDeviceStats:  # pylint: disable=too-many-instance-attributes
    """Hold forward device statistics for each time_slot. This class is used to first
    calculate the current results of device in the market and then used to merge it
    with the global results."""

    device_uuid: str
    time_slot: DateTime  # delivery time
    current_time_slot: DateTime

    # SELLER
    total_energy_produced: float = 0
    total_sell_trade_count: int = 0
    total_energy_sold: float = 0
    total_earned_eur: float = 0
    accumulated_sell_trade_rates: float = 0

    # BUYER
    total_energy_consumed: float = 0
    total_buy_trade_count: int = 0
    total_energy_bought: float = 0
    total_spent_eur: float = 0
    accumulated_buy_trade_rates: float = 0

    def __post_init__(self):
        """Creates non-field attributes for the objects which are needed for further
        operations e.g. TimeSeries generation, but should not be included in DB."""
        self.open_bids: List[Dict] = []
        self.open_offers: List[Dict] = []
        self.trades: List[Dict] = []

    def __add__(self, other: "ForwardDeviceStats"):
        assert self.time_slot == other.time_slot
        assert self.device_uuid == other.device_uuid

        if self.current_time_slot > other.current_time_slot:
            current_time_slot = self.current_time_slot
            open_bids = self.open_bids
            open_offers = self.open_offers
        elif self.current_time_slot < other.current_time_slot:
            current_time_slot = other.current_time_slot
            open_bids = other.open_bids
            open_offers = other.open_offers
        else:
            raise AssertionError(
                "Adding objects with same `current_time_slot` is not possible.")

        forward_device_stats = ForwardDeviceStats(
            time_slot=self.time_slot,
            device_uuid=self.device_uuid,
            current_time_slot=current_time_slot,
            total_energy_produced=self.total_energy_produced + other.total_energy_produced,
            total_sell_trade_count=self.total_sell_trade_count + other.total_sell_trade_count,
            total_energy_sold=self.total_energy_sold + other.total_energy_sold,
            total_earned_eur=self.total_earned_eur + other.total_earned_eur,
            total_energy_consumed=self.total_energy_consumed + other.total_energy_consumed,
            total_buy_trade_count=self.total_buy_trade_count + other.total_buy_trade_count,
            total_energy_bought=self.total_energy_bought + other.total_energy_bought,
            total_spent_eur=self.total_spent_eur + other.total_spent_eur,
            accumulated_buy_trade_rates=(self.accumulated_buy_trade_rates +
                                         other.accumulated_buy_trade_rates),
            accumulated_sell_trade_rates=(self.accumulated_sell_trade_rates +
                                          other.accumulated_sell_trade_rates)
        )
        forward_device_stats.open_bids = open_bids
        forward_device_stats.open_offers = open_offers
        forward_device_stats.trades = self.trades + other.trades

        return forward_device_stats

    def to_dict(self) -> Dict:
        """Generate a dictionary for saving the data into DB."""
        result_dict = {f.name: getattr(self, f.name) for f in fields(self)}
        result_dict["time_slot"] = format_datetime(result_dict["time_slot"])
        result_dict["current_time_slot"] = format_datetime(
            result_dict["current_time_slot"])
        return result_dict

    @classmethod
    def from_dict(cls, device_stats_dict: Dict) -> "ForwardDeviceStats":
        """Return ForwardDeviceStats from dict, with deserialized DateTimes
        from YYYY-MM-DDTHH:mm format."""
        time_slot = device_stats_dict.get("time_slot")
        current_time_slot = device_stats_dict.get("current_time_slot")
        if time_slot:
            device_stats_dict["time_slot"] = str_to_pendulum_datetime(time_slot)
        if current_time_slot:
            device_stats_dict["current_time_slot"] = str_to_pendulum_datetime(current_time_slot)
        return ForwardDeviceStats(**device_stats_dict)

    def add_trade(self, trade: Dict) -> None:
        """Add trade information to device stats."""
        assert str_to_pendulum_datetime(trade["time_slot"]) == self.time_slot

        if trade["seller"]["uuid"] == self.device_uuid:
            self.total_sell_trade_count += 1
            self.total_energy_sold += trade["energy"]
            self.total_earned_eur += trade["price"]
            self.accumulated_sell_trade_rates += trade["energy_rate"]
            self.trades.append(trade)
        elif trade["buyer"]["uuid"] == self.device_uuid:
            self.total_buy_trade_count += 1
            self.total_energy_bought += trade["energy"]
            self.total_spent_eur += trade["price"]
            self.accumulated_buy_trade_rates += trade["energy_rate"]
            self.trades.append(trade)
        else:
            raise AssertionError("Device is not seller/buyer of the trade.")

    def add_bid(self, bid: Dict) -> None:
        """Add bid information to device stats."""
        assert str_to_pendulum_datetime(bid["time_slot"]) == self.time_slot
        assert bid["buyer"]["uuid"] == self.device_uuid, "Device is not buyer of the bid."
        self.open_bids.append(bid)

    def add_offer(self, offer: Dict) -> None:
        """Add offer information to device stats."""
        assert str_to_pendulum_datetime(offer["time_slot"]) == self.time_slot
        assert offer["seller"]["uuid"] == self.device_uuid, "Device is not seller of the offer."
        self.open_offers.append(offer)

    @property
    def average_sell_rate(self) -> float:
        """Return average sell price for the timeslot."""
        if self.total_sell_trade_count == 0:
            return 0
        return self.accumulated_sell_trade_rates / self.total_sell_trade_count

    @property
    def average_buy_rate(self) -> float:
        """Return average buy price for the timeslot."""
        if self.total_buy_trade_count == 0:
            return 0
        return self.accumulated_buy_trade_rates / self.total_buy_trade_count


def handle_forward_results(
        current_time_slot: DateTime, market_stats: Dict[str, Dict[str, List]]) -> Dict:
    """Group trades by time_slot and device_uuid to accumulate orders for each device."""
    result = defaultdict(dict)

    if not market_stats:
        return result

    for time_slot_str, time_slot_stats in market_stats.items():
        time_slot = str_to_pendulum_datetime(time_slot_str)
        for trade in time_slot_stats["trades"]:
            buyer_id = trade["buyer"]["uuid"]
            seller_id = trade["seller"]["uuid"]

            if seller_id not in result[time_slot]:
                result[time_slot][seller_id] = ForwardDeviceStats(
                    time_slot=time_slot, device_uuid=seller_id,
                    current_time_slot=current_time_slot)
            result[time_slot][seller_id].add_trade(trade)

            if buyer_id not in result[time_slot]:
                result[time_slot][buyer_id] = ForwardDeviceStats(
                    time_slot=time_slot, device_uuid=buyer_id, current_time_slot=current_time_slot)
            result[time_slot][buyer_id].add_trade(trade)

        for bid in time_slot_stats["bids"]:
            buyer_id = bid["buyer"]["uuid"]
            if buyer_id not in result[time_slot]:
                result[time_slot][buyer_id] = ForwardDeviceStats(
                    time_slot=time_slot, device_uuid=buyer_id, current_time_slot=current_time_slot)
            result[time_slot][buyer_id].add_bid(bid)

        for offer in time_slot_stats["offers"]:
            seller_id = offer["seller"]["uuid"]
            if seller_id not in result[time_slot]:
                result[time_slot][seller_id] = ForwardDeviceStats(
                    time_slot=time_slot, device_uuid=seller_id,
                    current_time_slot=current_time_slot)
            result[time_slot][seller_id].add_offer(offer)

    return result
