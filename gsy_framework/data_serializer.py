import pickle
from zlib import compress, decompress
from typing import Dict


class DataSerializer:
    """Custom Serializer / Deserializer."""
    @staticmethod
    def encode_and_compress_dict(uncompressed_dict: Dict) -> bytes:
        """Convert a dict into str by pickling and compressing."""
        pickled_str = pickle.dumps(uncompressed_dict)
        return compress(pickled_str)

    @staticmethod
    def decompress_and_decode(compressed_dict: bytes) -> Dict:
        """Decompress and decode data sent via redis queue."""
        return pickle.loads(decompress(compressed_dict))
