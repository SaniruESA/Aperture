import python.server as server
import python.log as logger
from python.log.basic_logs import *

logger.set_stdout()

client = server.Client()

send = {"type":"message","content":"Hello!"}
client.verify()
info(client.recv())
send = {"type":"exit"}
client.send_json(send)
info(client.recv())