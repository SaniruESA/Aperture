import python_acc_lib.server as server
from python_acc_lib.server import easy_client
import python_acc_lib.logger as logger
from python_acc_lib.logger.basic_logs import *
import time

if __name__ == "__main__":

    logger.set_stdout()

    client = easy_client.generate_client()
    
    easy_client.add_button([0,0,50,50],"Button Numero Uno")
    easy_client.add_button([500,500,100,50],"Button 2")
    easy_client.update_window([50,50,1000,1000])
    easy_client.add_popup("Hello!")
    
    while True:
        time.sleep(0.1)