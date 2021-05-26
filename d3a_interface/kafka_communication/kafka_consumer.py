import json
from zlib import decompress

from kafka import KafkaConsumer

from d3a_interface.kafka_communication import KAFKA_URL, DEFAULT_KAFKA_URL, KAFKA_USERNAME, \
    KAFKA_PASSWORD, KAFKA_COMMUNICATION_SECURITY_PROTOCOL, KAFKA_SASL_AUTH_MECHANISM, \
    KAFKA_API_VERSION, create_kafka_new_ssl_context, KAFKA_TOPIC

KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC = 64 * 1024 * 1024
KAFKA_MAX_POLL_RECORDS = 10


class KafkaConnection:
    def __init__(self, callback):
        if KAFKA_URL != DEFAULT_KAFKA_URL:
            kwargs = {"bootstrap_servers": KAFKA_URL,
                      "sasl_plain_username": KAFKA_USERNAME,
                      "sasl_plain_password": KAFKA_PASSWORD,
                      "security_protocol": KAFKA_COMMUNICATION_SECURITY_PROTOCOL,
                      "ssl_context": create_kafka_new_ssl_context(),
                      "sasl_mechanism": KAFKA_SASL_AUTH_MECHANISM,
                      "api_version": KAFKA_API_VERSION,
                      "fetch_max_bytes": KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC,
                      "max_partition_fetch_bytes": KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC,
                      "max_poll_records": KAFKA_MAX_POLL_RECORDS}
        else:
            kwargs = {"bootstrap_servers": DEFAULT_KAFKA_URL}

        self._consumer = KafkaConsumer(KAFKA_TOPIC, **kwargs)
        self._callback = callback

    def execute_cycle(self):
        for msg in self._consumer:
            payload = json.loads(decompress(msg.value).decode("utf-8"))
            self._callback(payload)
