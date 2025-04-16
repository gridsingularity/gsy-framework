import json
import logging
import os
import uuid

import requests
from tabulate import tabulate

from gsy_framework.constants_limits import JWT_TOKEN_EXPIRY_IN_SECS
from gsy_framework.utils import RepeatingTimer


def get_request(endpoint, data, jwt_token):
    resp = requests.get(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json", "Authorization": f"JWT {jwt_token}"},
    )
    return resp.json() if request_response_returns_http_2xx(endpoint, resp) else None


def post_request(endpoint, data, jwt_token):
    resp = requests.post(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json", "Authorization": f"JWT {jwt_token}"},
    )
    return resp.json() if request_response_returns_http_2xx(endpoint, resp) else None


def blocking_get_request(endpoint, data, jwt_token):
    data["transaction_id"] = str(uuid.uuid4())
    resp = requests.get(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json", "Authorization": f"JWT {jwt_token}"},
    )

    return resp.json() if request_response_returns_http_2xx(endpoint, resp) else None


def blocking_post_request(endpoint, data, jwt_token):
    data["transaction_id"] = str(uuid.uuid4())
    resp = requests.post(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json", "Authorization": f"JWT {jwt_token}"},
    )
    return json.loads(resp.text) if request_response_returns_http_2xx(endpoint, resp) else None


def request_response_returns_http_2xx(endpoint, resp):
    if 200 <= resp.status_code <= 299:
        return True
    logging.error(
        "Request to %s failed with status code %s. Response body: %s",
        endpoint,
        resp.status_code,
        resp.text,
    )
    return False


def retrieve_jwt_key_from_server(domain_name):
    resp = requests.post(
        f"{domain_name}/api-token-auth/",
        data=json.dumps(
            {
                "username": os.environ["API_CLIENT_USERNAME"],
                "password": os.environ["API_CLIENT_PASSWORD"],
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    if resp.status_code != 200:
        logging.error(
            "Request for token authentication failed with status code %s. Response body: %s",
            resp.status_code,
            resp.text,
        )
        return ""

    return resp.json()["access"]


class RestCommunicationMixin:

    def _create_jwt_refresh_timer(self, sim_api_domain_name):
        self.jwt_refresh_timer = RepeatingTimer(
            # By refreshing 3 times during the lifetime of a token,
            # we assure that we always have a working JWT token.
            JWT_TOKEN_EXPIRY_IN_SECS / 4,
            self._refresh_jwt_token,
            [sim_api_domain_name],
        )
        self.jwt_refresh_timer.daemon = True
        self.jwt_refresh_timer.start()

    def _refresh_jwt_token(self, domain_name):
        self.jwt_token = retrieve_jwt_key_from_server(domain_name)

    def _post_request(self, endpoint, data):
        endpoint = f"{endpoint}/"
        data["transaction_id"] = str(uuid.uuid4())
        return data["transaction_id"], post_request(endpoint, data, self.jwt_token)

    def _get_request(self, endpoint, data):
        endpoint = f"{endpoint}"
        data["transaction_id"] = str(uuid.uuid4())
        return data["transaction_id"], get_request(endpoint, data, self.jwt_token)


def get_slot_completion_percentage_int_from_message(message):
    """Extract the `slot_completion` percentage from message and return the value."""

    if "slot_completion" in message:
        return int(message["slot_completion"].split("%")[0])
    return ""


def log_market_progression(message: dict) -> None:
    """Receive an event message and log ticks-market cycles info."""

    try:
        event = message.get("event", None)
        if event not in ["tick", "market", "market_cycle"]:
            return
        headers = [
            "event",
        ]
        table_data = [
            event,
        ]
        data_dict = message.get("content") if "content" in message.keys() else message

        # TODO: "start_time" key will be deprecated
        #  once the non-aggregator connection is deprecated
        if "start_time" in data_dict:
            headers.extend(
                [
                    "start_time",
                    "duration_min",
                ]
            )
            table_data.extend([data_dict.get("start_time"), data_dict.get("duration_min")])

        if "slot_completion" in data_dict:
            headers.append("slot_completion")
            table_data.append(data_dict.get("slot_completion"))

        if event in ["market", "market_cycle"] and "market_slot" in data_dict:
            headers.extend(["market_slot"])
            table_data.extend([data_dict.get("market_slot")])

        if event == "tick":
            slot_completion_int = get_slot_completion_percentage_int_from_message(message)
            if slot_completion_int is not None and slot_completion_int < 10:
                return

        logging.info(f"\n\n{tabulate([table_data, ], headers=headers, tablefmt='fancy_grid')}\n\n")
    except Exception as exception:
        logging.warning("Error while logging market progression %s", exception)
