import os
import time
import python_acc_lib.server.easy_client as easy_client
import python_acc_lib.logger as logger

# Run server
os.system("start python -m python_acc_lib")

if __name__ == "__main__":
    
    # Set logging location
    logger.set_stdout()

    # Generate client
    generated = False
    max_generate_times = 0
    
    while not generated:
        max_generate_times += 1
        if max_generate_times > 10:
            quit()
        try:
            client = easy_client.generate_client()
            generated = True
        except:
            time.sleep(1)
    
    # Add buttons
    easy_client.add_button([0,0,50,50],"Button Numero Uno")
    easy_client.add_button([300, 540, 250, 150],"Home Page")
    
    # Change window location
    easy_client.update_window([50,50,1000,1000])
    
    # Add popup
    easy_client.add_popup("Hello!",(0,0,0),(255,255,255),(250,300))
    
    # Wait
    while True:
        time.sleep(0.1)