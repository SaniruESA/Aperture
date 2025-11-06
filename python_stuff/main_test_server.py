import python_acc_lib.server as server
import python_acc_lib.logger as logger
from python_acc_lib.logger.basic_logs import *

logger.set_stdout()

serv = server.Server()

serv.accept()

serv.tick_threaded()
serv.tick_pyglet()