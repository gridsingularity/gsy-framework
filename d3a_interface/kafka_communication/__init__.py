import ssl
from os import environ

DEFAULT_KAFKA_URL = 'localhost:9092'
KAFKA_URL = environ.get('KAFKA_URL', DEFAULT_KAFKA_URL)
KAFKA_USERNAME = environ.get('KAFKA_USERNAME', None)
KAFKA_PASSWORD = environ.get('KAFKA_PASSWORD', None)
KAFKA_COMMUNICATION_SECURITY_PROTOCOL = \
    environ.get('KAFKA_COMMUNICATION_SECURITY_PROTOCOL', 'SASL_SSL')
KAFKA_SASL_AUTH_MECHANISM = \
    environ.get('KAFKA_SASL_AUTH_MECHANISM', 'SCRAM-SHA-512')
KAFKA_API_VERSION = (0, 10)
KAFKA_TOPIC = 'd3a-results'


def create_kafka_new_ssl_context():
    # Create a new context using system defaults, disable all but TLS1.2
    ssl_context = ssl.create_default_context()
    ssl_context.options &= ssl.OP_NO_TLSv1
    ssl_context.options &= ssl.OP_NO_TLSv1_1
    return ssl_context
