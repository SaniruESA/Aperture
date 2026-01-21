import aperture_library.server as server
from aperture_library.server import easy_client
import aperture_library.logger as logger
from aperture_library.logger.basic_logs import *
import time

if __name__ == "__main__":

    logger.set_stdout()

    client = easy_client.generate_client()
    
    easy_client.add_button([0,0,50,50],"Button Numero Uno")
    easy_client.add_button([300, 1400, 250, 150],"Home Page")
    easy_client.update_window([50,50,1000,500])
    easy_client.add_popup("Hello!",(0,0,0),(255,255,255),(250,300))
    
    while True:
        time.sleep(0.1)