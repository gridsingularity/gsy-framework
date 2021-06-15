import json
import logging
import os
import uuid

import requests
from d3a_interface.constants_limits import JWT_TOKEN_EXPIRY_IN_SECS
from d3a_interface.utils import RepeatingTimer


def get_request(endpoint, data, jwt_token):
    resp = requests.get(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json",
                 "Authorization": f"JWT {jwt_token}"})
    return resp.json() if request_response_returns_http_2xx(endpoint, resp) else None


def post_request(endpoint, data, jwt_token):
    resp = requests.post(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json",
                 "Authorization": f"JWT {jwt_token}"})
    return resp.json() if request_response_returns_http_2xx(endpoint, resp) else None


def blocking_get_request(endpoint, data, jwt_token):
    data["transaction_id"] = str(uuid.uuid4())
    resp = requests.get(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json",
                 "Authorization": f"JWT {jwt_token}"})

    return resp.json() if request_response_returns_http_2xx(endpoint, resp) else None


def blocking_post_request(endpoint, data, jwt_token):
    data["transaction_id"] = str(uuid.uuid4())
    resp = requests.post(
        endpoint,
        data=json.dumps(data),
        headers={"Content-Type": "application/json",
                 "Authorization": f"JWT {jwt_token}"})
    return json.loads(resp.text) if request_response_returns_http_2xx(endpoint, resp) else None


def request_response_returns_http_2xx(endpoint, resp):
    if 200 <= resp.status_code <= 299:
        return True
    else:
        logging.error(f"Request to {endpoint} failed with status code {resp.status_code}. "
                      f"Response body: {resp.text}")
        return False


def retrieve_jwt_key_from_server(domain_name):
    resp = requests.post(
        f"{domain_name}/api-token-auth/",
        data=json.dumps({"username": os.environ["API_CLIENT_USERNAME"],
                         "password": os.environ["API_CLIENT_PASSWORD"]}),
        headers={"Content-Type": "application/json"})
    if resp.status_code != 200:
        logging.error(f"Request for token authentication failed with status "
                      f"code {resp.status_code}."
                      f"Response body: {resp.text}")
        return

    return resp.json()["token"]


class RestCommunicationMixin:

    def _create_jwt_refresh_timer(self, sim_api_domain_name):
        self.jwt_refresh_timer = RepeatingTimer(
            JWT_TOKEN_EXPIRY_IN_SECS - 30, self._refresh_jwt_token, [sim_api_domain_name]
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
