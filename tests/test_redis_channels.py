import os
from gsy_framework.redis_channels import QueueNames


class TestRedisChannels:

    @staticmethod
    def teardown_method():
        os.environ.pop("LISTEN_TO_CANARY_NETWORK_REDIS_QUEUE", None)
        os.environ.pop("LISTEN_TO_PAID_CUSTOMER_REDIS_QUEUE", None)

    @staticmethod
    def test_gsy_e_queue_name():
        assert QueueNames().gsy_e_queue_name == "exchange"
        os.environ["LISTEN_TO_CANARY_NETWORK_REDIS_QUEUE"] = "no"
        os.environ["LISTEN_TO_PAID_CUSTOMER_REDIS_QUEUE"] = "yes"
        assert QueueNames().gsy_e_queue_name == "exchange-paid"
        os.environ["LISTEN_TO_CANARY_NETWORK_REDIS_QUEUE"] = "yes"
        assert QueueNames().gsy_e_queue_name == "canary_network"
