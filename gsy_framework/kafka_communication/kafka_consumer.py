import json
from zlib import decompress

from kafka import KafkaConsumer

from gsy_framework.kafka_communication import (
    KAFKA_URL, IS_KAFKA_RUNNING_LOCALLY, KAFKA_USERNAME,
    KAFKA_PASSWORD, KAFKA_COMMUNICATION_SECURITY_PROTOCOL,
    KAFKA_SASL_AUTH_MECHANISM,
    KAFKA_API_VERSION, create_kafka_new_ssl_context, KAFKA_RESULTS_TOPIC, KAFKA_CONSUMER_GROUP_ID)

KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC = 64 * 1024 * 1024
KAFKA_MAX_POLL_RECORDS = 10
KAFKA_CONSUMER_TIMEOUT_MS = 50


class KafkaConnection:
    def __init__(self, callback):
        if IS_KAFKA_RUNNING_LOCALLY:
            kwargs = {"bootstrap_servers": KAFKA_URL,
                      "consumer_timeout_ms": KAFKA_CONSUMER_TIMEOUT_MS}
        else:
            kwargs = {"bootstrap_servers": KAFKA_URL,
                      "sasl_plain_username": KAFKA_USERNAME,
                      "sasl_plain_password": KAFKA_PASSWORD,
                      "security_protocol": KAFKA_COMMUNICATION_SECURITY_PROTOCOL,
                      "ssl_context": create_kafka_new_ssl_context(),
                      "sasl_mechanism": KAFKA_SASL_AUTH_MECHANISM,
                      "api_version": KAFKA_API_VERSION,
                      "fetch_max_bytes": KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC,
                      "max_partition_fetch_bytes": KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC,
                      "max_poll_records": KAFKA_MAX_POLL_RECORDS,
                      "consumer_timeout_ms": KAFKA_CONSUMER_TIMEOUT_MS,
                      "group_id": KAFKA_CONSUMER_GROUP_ID}

        self._consumer = KafkaConsumer(KAFKA_RESULTS_TOPIC, **kwargs)
        self._callback = callback

    def execute_cycle(self):
        for msg in self._consumer:
            payload = json.loads(decompress(msg.value).decode("utf-8"))
            self._callback(payload)
