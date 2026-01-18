import python_acc_lib.server as server
import python_acc_lib.logger as logger
from python_acc_lib.logger.basic_logs import *

if __name__ == "__main__":
    logger.set_stdout()
    logger.clear()

    server.fast_start()