import aperture_library.server as server
import aperture_library.logger as logger
from aperture_library.logger.basic_logs import *

if __name__ == "__main__":
    logger.set_stdout()
    logger.clear()

    server.fast_start()