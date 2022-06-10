"""Module containing classes to convert geographical addresses into coordinates."""

import logging
import os
from typing import Tuple

import requests

import geocoder

logger = logging.getLogger(__name__)


class LocationConverterException(Exception):
    """Exception raised while converting a location/address into its coordinates."""


class LocationConverter:
    """Class to convert location to geographical coordinates."""

    def __init__(self):
        try:
            self._key = os.environ["MAPBOX_API_KEY"]
        except KeyError as ex:
            message = (
                "The Mapbox API key (MAPBOX_API_KEY) was not found in the environment. "
                "Can't proceed with the detection of PV coordinates for the community datasheet.")
            raise LocationConverterException(message) from ex

    def convert(self, address: str, session=None) -> Tuple[float, float]:
        """Convert an address to its geographical coordinates."""
        try:
            results = geocoder.mapbox(address, session=session, key=self._key)
        except requests.exceptions.RequestException as ex:
            raise LocationConverterException(
                f"Connection error while requesting coordinates for {address}.") from ex

        if not results.ok:
            raise LocationConverterException(
                f"Error while requesting coordinates for {address}: {results.status}")

        # We flip the coordinates because that's how gsy-web expects them in `geo_tag_location`
        latitude, longitude = results.latlng
        return (longitude, latitude)
