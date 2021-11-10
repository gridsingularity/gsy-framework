import logging
import sys

import gsy_framework

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(console_handler)

logger.warning(
    "The d3a_interface module name will be deprecated soon. Please use gsy_framework instead.")

__all__ = ["gsy_framework"]

sys.modules[__name__] = sys.modules["gsy_framework"]
