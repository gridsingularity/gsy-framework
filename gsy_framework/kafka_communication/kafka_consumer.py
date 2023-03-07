import logging
import json
import traceback
from zlib import decompress

from kafka import KafkaConsumer
from kafka.structs import OffsetAndMetadata

from gsy_framework.kafka_communication import (
    KAFKA_URL, IS_KAFKA_RUNNING_LOCALLY, KAFKA_USERNAME,
    KAFKA_PASSWORD, KAFKA_COMMUNICATION_SECURITY_PROTOCOL,
    KAFKA_SASL_AUTH_MECHANISM,
    KAFKA_API_VERSION, create_kafka_new_ssl_context, KAFKA_RESULTS_TOPIC, KAFKA_CONSUMER_GROUP_ID)

KAFKA_MAX_MESSAGE_SIZE_PER_TOPIC = 64 * 1024 * 1024
KAFKA_MAX_POLL_RECORDS = 1
KAFKA_CONSUMER_TIMEOUT_MS = 50

RESULTS_SERVICE_RETRY_COUNT = 3

logger = logging.getLogger(__name__)


class KafkaConnection:
    """Kafka consumer class. Connect to a topic, read and process messages from it."""
    def __init__(self, callback):
        if IS_KAFKA_RUNNING_LOCALLY:
            kwargs = {"bootstrap_servers": KAFKA_URL,
                      "consumer_timeout_ms": KAFKA_CONSUMER_TIMEOUT_MS,
                      "group_id": KAFKA_CONSUMER_GROUP_ID,
                      "enable_auto_commit": False,
                      "max_poll_records": KAFKA_MAX_POLL_RECORDS}
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
                      "group_id": KAFKA_CONSUMER_GROUP_ID,
                      "enable_auto_commit": False}

        self._consumer = KafkaConsumer(KAFKA_RESULTS_TOPIC, **kwargs)
        self._callback = callback

    @staticmethod
    def _deserialize_message(msg):
        return json.loads(decompress(msg.value).decode("utf-8"))

    def _get_topic_partition(self):
        topic_partitions = self._consumer.assignment()
        if len(topic_partitions) != 1:
            # More than one partitions are connected to this consumer, this needs to be
            # reported as error.
            logger.error(
                "Consumer was connected to more than one topic / partition: %s",
                topic_partitions)
        return list(topic_partitions)[0]

    def _process_message_with_retries(self, msg):
        was_processed_correctly = False
        retry_counter = 0
        while not was_processed_correctly and retry_counter < RESULTS_SERVICE_RETRY_COUNT:
            # Try to process the message multiple times. Omit the message if it does not
            # succeed.
            try:
                payload = self._deserialize_message(msg)
                self._callback(payload)
                was_processed_correctly = True
            # pylint: disable=broad-except
            except Exception as ex:
                retry_counter += 1
                logger.error(
                    "Simulation results service ailed to process incoming message. %s. "
                    "Traceback: %s", str(ex), traceback.format_exc())

    def execute_cycle(self):
        """Main execution cycle of the Kafka consumer."""
        for msg in self._consumer:
            topic_partition = self._get_topic_partition()
            self._process_message_with_retries(msg)
            # Commit the message even though it has not been processed, since it failed in
            # multiple retries.
            self._consumer.commit({
                topic_partition: OffsetAndMetadata(msg.offset + 1, None)
            })
