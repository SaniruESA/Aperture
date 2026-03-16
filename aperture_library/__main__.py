"""
Quickly runs the server
"""

from . import server
from . import logger
from .logger.basic_logs import *

if __name__ == "__main__":
    logger.set_stdout()
    logger.clear()
    print("\x1b[2J\x1b[HServer Starting...", end="")

    server.fast_start()
