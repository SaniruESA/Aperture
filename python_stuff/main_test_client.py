import python_acc_lib.server as server
import python_acc_lib.logger as logger
from python_acc_lib.logger.basic_logs import *
import time
import python_acc_lib

if __name__ == "__main__":

    logger.set_stdout()

    client = server.Client()
    
    client.verify()
    info(client.recv(),__name__)
    send = {"type":"add_button","content":"[0,0,50,50]","name":"Button Numero Uno"}
    client.send_json(send)
    info(client.recv(),__name__)
    send = {"type":"add_button","content":"[100,100,50,50]","name":"Button 2"}
    client.send_json(send)
    info(client.recv(),__name__)
    while True:
        time.sleep(0.1)