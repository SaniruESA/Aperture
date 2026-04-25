"""
Client of Aperture Library for testing purposes.
"""

import aperture_library.server as server
from aperture_library.server import easy_client
import aperture_library.logger as logger
from aperture_library.logger.basic_logs import *
import time

if __name__ == "__main__":

    logger.set_stdout()

    client = easy_client.generate_client()

    easy_client.add_button([0, 0, 50, 50], "Button Numero Uno")
    easy_client.add_button([300, 500, 250, 150], "Home Page")
    easy_client.add_button([600, 500, 250, 150], "Exit Home Page")
    easy_client.update_window([50, 50, 1000, 500])
    easy_client.add_popup("Hello!", (0, 0, 0), (255, 255, 255), (250, 300))
    time.sleep(5)
    easy_client.toggle_subtitles(False)
    print(easy_client.list_voices())
    print(easy_client.set_default_voice("en-GB-ThomasNeural"))
    easy_client.add_popup("Test 2")

    while True:
        time.sleep(0.1)
