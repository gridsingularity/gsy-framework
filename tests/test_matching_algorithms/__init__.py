import uuid
from typing import Optional

from pendulum import DateTime

from gsy_framework.data_classes import Bid, Offer, TraderDetails


def offer_factory(additional_data: Optional[dict] = None):
    """Create and return an offer object from default and input values."""
    additional_data = additional_data or {}
    return Offer(
        **{"id": str(uuid.uuid4()),
           "creation_time": DateTime.now(),
           "time_slot": DateTime.now(),
           "price": 10,
           "energy": 30,
           "seller": TraderDetails(
                name="seller",
                uuid="seller_id",
                origin="seller",
                origin_uuid="seller_id",
           ),
           **additional_data})


def bid_factory(additional_data: Optional[dict] = None):
    """Create and return a bid object from default and input values."""
    additional_data = additional_data or {}
    return Bid(
        **{"id": str(uuid.uuid4()),
           "creation_time": DateTime.now(),
           "time_slot": DateTime.now(),
           "price": 10,
           "energy": 30,
           "buyer": TraderDetails(
                name="buyer",
                uuid="buyer_id",
                origin="buyer",
                origin_uuid="buyer_id",
           ),
           **additional_data})
