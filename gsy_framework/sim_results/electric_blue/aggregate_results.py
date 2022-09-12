from collections import defaultdict
from dataclasses import dataclass, fields
from typing import Dict, List

from gsy_framework.enums import AggregationResolution, AvailableMarketTypes

# Used by forward markets; the following dictionary defines
# what aggregations are needed for each market type.
MARKET_RESOLUTIONS = {
    AvailableMarketTypes.YEAR_FORWARD: [AggregationResolution.RES_1_MONTH],
    AvailableMarketTypes.MONTH_FORWARD: [AggregationResolution.RES_1_DAY],
    AvailableMarketTypes.WEEK_FORWARD: [AggregationResolution.RES_1_DAY]
}


@dataclass
class ForwardDeviceStats:  # pylint: disable=too-many-instance-attributes
    """Hold forward device statistics for each timeslot. This class is used to first
    calculate the current results of device in the market and then used to merge it
    with the global results."""
    timeslot: str
    device_uuid: str

    # SELLER
    total_energy_produced: float = 0
    total_sell_trade_count: int = 0
    total_energy_sold: float = 0
    total_earned_eur: float = 0
    # BUYER
    total_energy_consumed: float = 0
    total_buy_trade_count: int = 0
    total_energy_bought: float = 0
    total_spent_eur: float = 0

    def __add__(self, other: "ForwardDeviceStats"):
        assert self.timeslot == other.timeslot

        return ForwardDeviceStats(
            timeslot=self.timeslot,
            device_uuid=self.device_uuid,
            total_energy_produced=self.total_energy_produced + other.total_energy_produced,
            total_sell_trade_count=self.total_sell_trade_count + other.total_sell_trade_count,
            total_energy_sold=self.total_energy_sold + other.total_energy_sold,
            total_earned_eur=self.total_earned_eur + other.total_earned_eur,
            total_energy_consumed=self.total_energy_consumed + other.total_energy_consumed,
            total_buy_trade_count=self.total_buy_trade_count + other.total_buy_trade_count,
            total_energy_bought=self.total_energy_bought + other.total_energy_bought,
            total_spent_eur=self.total_spent_eur + other.total_spent_eur
        )

    def to_dict(self) -> Dict:
        """Generate a dictionary for saving the data into DB."""
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def add_trade(self, trade: Dict) -> None:
        """Add trade information to device stats."""
        if trade["seller_id"] == self.device_uuid:
            self.total_sell_trade_count += 1
            self.total_energy_sold += trade["energy"]
            self.total_earned_eur += trade["price"]
        elif trade["buyer_id"] == self.device_uuid:
            self.total_buy_trade_count += 1
            self.total_energy_bought += trade["energy"]
            self.total_spent_eur += trade["price"]


def handle_forward_results(market_stats: Dict[str, Dict[str, List]]) -> Dict:
    """Group trades by timeslot and device_uuid to accumulate trades for each device."""
    result = defaultdict(dict)

    if not market_stats:
        return result

    for timeslot, timeslot_stats in market_stats.items():
        for trade in timeslot_stats["trades"]:
            buyer_id = trade["buyer_id"]
            seller_id = trade["seller_id"]

            if seller_id not in result[timeslot]:
                result[timeslot][seller_id] = ForwardDeviceStats(
                    timeslot=timeslot, device_uuid=seller_id)

            if buyer_id not in result[timeslot]:
                result[timeslot][buyer_id] = ForwardDeviceStats(
                    timeslot=timeslot, device_uuid=buyer_id)

            result[timeslot][seller_id].add_trade(trade)
            result[timeslot][buyer_id].add_trade(trade)

    return result
