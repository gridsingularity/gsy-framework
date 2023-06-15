# pylint: disable=missing-function-docstring
from dataclasses import dataclass
import os


class SimulationCommandChannels:
    """Channels for simulation commands"""

    def __init__(self, simulation_id: str):
        self._simulation_id = simulation_id

    @property
    def pause(self) -> str:
        return f"{self._simulation_id}/pause"

    @property
    def stop(self) -> str:
        return f"{self._simulation_id}/stop"

    @property
    def resume(self) -> str:
        return f"{self._simulation_id}/resume"

    @property
    def reset(self) -> str:
        return f"{self._simulation_id}/reset"

    @property
    def live_event(self) -> str:
        return f"{self._simulation_id}/live-event"

    @property
    def bulk_live_event(self) -> str:
        return f"{self._simulation_id}/bulk-live-event"

    @property
    def area_map(self) -> str:
        return f"{self._simulation_id}/area-map"

    def response_channel(self, command_type) -> str:
        return f"{self._simulation_id}/response/{command_type}"


class MatchingEngineChannels:
    """Channels for external matching engine"""

    def __init__(self, simulation_id: str):
        self._simulation_id = simulation_id

    @property
    def events(self) -> str:
        return f"external-matching-engine/{self._simulation_id}/events/"

    @property
    def offers_bids(self) -> str:
        return f"external-matching-engine/{self._simulation_id}/offers-bids/"

    @property
    def recommendations(self) -> str:
        return f"external-matching-engine/{self._simulation_id}/recommendations/"

    @property
    def response(self) -> str:
        return f"external-matching-engine/{self._simulation_id}/response/"

    @property
    def simulation_id(self) -> str:
        return "external-matching-engine/simulation-id"

    @property
    def simulation_id_response(self) -> str:
        return "external-matching-engine/simulation_id/response/"


class ExternalStrategyChannels:
    # pylint: disable=too-many-public-methods
    """Channels for external device connection"""

    def __init__(self, communication_web: bool, config_uuid: str, asset_uuid: str = None,
                 asset_name: str = None):
        self._web = communication_web
        self._config_uuid = config_uuid
        self._asset_uuid = asset_uuid
        self._asset_name = asset_name

    @property
    def channel_prefix(self) -> str:
        """Prefix for the API endpoints."""
        if self._web:  # REST
            assert self._asset_uuid
            return f"external/{self._config_uuid}/{self._asset_uuid}"
        assert self._asset_name
        return f"{self._asset_name}"  # REDIS

    @property
    def register(self) -> str:
        return f"{self.channel_prefix}/register_participant"

    @property
    def unregister(self) -> str:
        return f"{self.channel_prefix}/unregister_participant"

    @property
    def register_response(self) -> str:
        return f"{self.channel_prefix}/response/register_participant"

    @property
    def unregister_response(self) -> str:
        return f"{self.channel_prefix}/response/unregister_participant"

    @property
    def device_info(self) -> str:
        return f"{self.channel_prefix}/device_info"

    @property
    def device_info_response(self) -> str:
        return f"{self.channel_prefix}/response/device_info"

    @property
    def energy_forecast(self) -> str:
        return f"{self.channel_prefix}/set_energy_forecast"

    @property
    def energy_measurement(self) -> str:
        return f"{self.channel_prefix}/set_energy_measurement"

    @property
    def offer(self) -> str:
        return f"{self.channel_prefix}/offer"

    @property
    def offer_response(self) -> str:
        return f"{self.channel_prefix}/response/offer"

    @property
    def delete_offer(self) -> str:
        return f"{self.channel_prefix}/delete_offer"

    @property
    def delete_offer_response(self) -> str:
        return f"{self.channel_prefix}/response/delete_offer"

    @property
    def list_offers(self) -> str:
        return f"{self.channel_prefix}/list_offers"

    @property
    def list_offers_response(self) -> str:
        return f"{self.channel_prefix}/response/list_offers"

    @property
    def bid(self) -> str:
        return f"{self.channel_prefix}/bid"

    @property
    def bid_response(self) -> str:
        return f"{self.channel_prefix}/response/bid"

    @property
    def delete_bid(self) -> str:
        return f"{self.channel_prefix}/delete_bid"

    @property
    def delete_bid_response(self) -> str:
        return f"{self.channel_prefix}/response/delete_bid"

    @property
    def list_bids(self) -> str:
        return f"{self.channel_prefix}/list_bids"

    @property
    def list_bids_response(self) -> str:
        return f"{self.channel_prefix}/response/list_bids"

    @property
    def dso_market_stats(self) -> str:
        return f"{self.channel_prefix}/dso_market_stats"

    @property
    def dso_market_stats_response(self) -> str:
        return f"{self.channel_prefix}/response/dso_market_stats"

    @property
    def grid_fees(self) -> str:
        return f"{self.channel_prefix}/grid_fees"

    @property
    def grid_fees_response(self) -> str:
        return f"{self.channel_prefix}/response/grid_fees"

    @property
    def tick(self) -> str:
        return f"{self.channel_prefix}/events/tick"

    @property
    def trade(self) -> str:
        return f"{self.channel_prefix}/events/trade"

    @property
    def finish(self) -> str:
        return f"{self.channel_prefix}/events/finish"

    @property
    def market(self) -> str:
        return f"{self.channel_prefix}/events/market"


class AggregatorChannels:
    """Channels for external aggregator connection"""

    def __init__(self, config_uuid: str = "", aggregator_uuid: str = ""):
        self._config_uuid = config_uuid
        self._aggregator_uuid = aggregator_uuid

    @property
    def events(self) -> str:
        return f"external-aggregator/{self._config_uuid}/{self._aggregator_uuid}/events/all"

    @property
    def response(self) -> str:
        return "aggregator-response"

    @property
    def batch_commands(self) -> str:
        return f"external-aggregator/{self._config_uuid}/batch_commands"

    @property
    def batch_commands_response(self) -> str:
        return f"external-aggregator/{self._config_uuid}/{self._aggregator_uuid}/" \
               "response/batch_commands"

    @property
    def commands(self) -> str:
        return "aggregator-commands"


@dataclass(frozen=True)
class ExchangeChannels:
    """Channels for general exchange communication"""

    errors = "gsy-e-errors"
    new_results = "new-results"
    user_notification = "notification"
    heart_beat = "gsy-e-heartbeat"


@dataclass(frozen=True)
class QueueNames:
    """Names for redis queues"""

    sdk_communication = os.environ.get("GSYE_SDK_EVENTS_RESPONSES_QUEUE", "sdk-events-responses")
    canary_job = os.environ.get("GSYE_CANARY_JOB_QUEUE", "canary_network")
    simulation_job = os.environ.get("GSYE_SIMULATION_JOB_QUEUE", "exchange")
    simulation_job_paid = os.environ.get("GSYE_PAID_SIMULATION_JOB_QUEUE", "exchange-paid")

    @property
    def gsy_e_queue_name(self):
        """Get simulation queue name."""
        if os.environ.get("LISTEN_TO_CANARY_NETWORK_REDIS_QUEUE", "no") == "yes":
            return self.canary_job
        if os.environ.get("LISTEN_TO_PAID_CUSTOMER_REDIS_QUEUE", "no") == "yes":
            return self.simulation_job_paid
        return self.simulation_job
