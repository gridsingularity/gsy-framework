"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from typing import Dict
from gsy_framework.data_serializer import DataSerializer


class TestDataSerializer:
    """Test compress and decompress dictionaries"""

    @staticmethod
    def test_encode_and_compress_dict():
        """Assert if data is bytes type"""
        data = {'key1': 'value1', 'key2': 'value2'}
        compressed_data = DataSerializer.encode_and_compress_dict(data)
        assert type(compressed_data) == bytes

    @staticmethod
    def test_decompress_and_decode():
        """Assert if data is dict type"""
        data = b'x\x9ck`\x99*\xcc\x00\x01\xb5Sz\xb8\x8a\xf3sSu\xcb\x12sJS\xa7xW\x17\xeb\x01\x00p\x08\x08\xcd'
        uncompressed_data = DataSerializer.decompress_and_decode(data)
        # assert type(uncompressed_data) == dict
        assert uncompressed_data == {'some-value': 123}
