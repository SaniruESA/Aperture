"""
Server of Aperture Library for testing purposes.
"""

from aperture_library import verify_lib

# For testing purposes
CHECK_LIBS = False
if CHECK_LIBS:
    verify_lib()

import aperture_library.server as server
import aperture_library.logger as logger
from aperture_library.logger.basic_logs import *

if __name__ == "__main__":
    logger.set_stdout()
    logger.clear()

    server.fast_start()
