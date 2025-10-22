import python.server as server
import python.log as logger
from python.log.basic_logs import *

logger.set_stdout()

serv = server.Server()

serv.accept()

while True:
    serv.tick_server()