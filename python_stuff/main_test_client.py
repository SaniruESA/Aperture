import python_acc_lib.server as server
import python_acc_lib.logger as logger
from python_acc_lib.logger.basic_logs import *
import time
import python_acc_lib

if __name__ == "__main__":

    logger.set_stdout()
    
    python_acc_lib.verify_lib()

    client = server.Client()
    
    client.verify()
    info(client.recv(),__name__)
    send = {"type":"generate_tts","content":"Hello, World!"}
    client.send_json(send)
    info(client.recv(),__name__)
    while True:
        time.sleep(0.1)