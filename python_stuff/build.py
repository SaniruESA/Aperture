import os
import time
import python_acc_lib.server.easy_client as easy_client
import python_acc_lib.logger as logger
import pygetwindow

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
    x_offset = 10
    y_offset = 10

    easy_client.add_button([1796 + x_offset, 34 + y_offset, 110, 40], "Login button")
    easy_client.add_button([1661 + x_offset, 34 + y_offset, 110, 40], "Sign Up button")
    easy_client.add_button([21 + x_offset, 165 + y_offset, 110, 40], "Dashboard button")
    easy_client.add_button([21 + x_offset, 223 + y_offset, 110, 40], "Profile button")
    easy_client.add_button([21 + x_offset, 281 + y_offset, 110, 40], "Settings button")
    easy_client.add_button([21 + x_offset, 339 + y_offset, 110, 40], "Help button")
    easy_client.add_button([21 + x_offset, 397 + y_offset, 110, 40], "Logout button")
    easy_client.add_button([296 + x_offset, 308 + y_offset, 110, 40], "Submit button")

    window:pygetwindow.Window = pygetwindow.getWindowsWithTitle("Modern Homepage")[0]
    
    # Add popup
    easy_client.add_popup("Please enter a valid email.",(0,0,0),(255,255,255),(960,540))
    
    # Wait
    while True:
        window_loc = [window.left,window.top,window.width,window.height]
        # Change window location
        easy_client.update_window()
        time.sleep(1)