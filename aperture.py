"""
Quickly runs the server
"""

from aperture_library import server
from aperture_library import logger
from aperture_library.logger.basic_logs import *
from aperture_library import library_checker

if __name__ == "__main__":
    library_checker.verify_lib()

    logger.set_stdout()
    logger.clear()
    print("\x1b[2J\x1b[HServer Starting...",end="")

    server.fast_start()