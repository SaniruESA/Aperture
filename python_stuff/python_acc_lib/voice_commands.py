from RealtimeSTT import AudioToTextRecorder
import json
from keyboard_nav import TabNavOrder
import pyautogui
from . import ui
import re

with open("python_stuff/python_acc_lib/intentions.json", "r") as file:
    intention_json = json.load(file)

# AUDIO_RECORDER = AudioToTextRecorder(language="en")

# def capture_audio():
#     # test for debugging purposes
#     voice_input = AUDIO_RECORDER.text()
#     print(voice_input)
#     return voice_input

# capture_audio()

# Functions to actually carry out the user's intention
def press_button(page_name: str): # this one doubles for pressing a button AND moving pages
    # Bad code incoming (fix / refactor later)
    all_buttons = TabNavOrder.getUIElements()["button"]

    page_button = [x for x in all_buttons if page_name in x["ariaText"]]

    if len(page_button) == 0:
        return
    else:
        # Press the button and return mouse to original location
        get_window()
        mousePos = pyautogui.position()
        rect:list = page_button[0]["rect"]
        pyautogui.click(rect[0]+rect[2]/2+win_x,rect[1]+rect[3]/2+win_y)
        print(rect[0]+rect[2]/2+win_x,rect[1]+rect[3]/2+win_y)
        pyautogui.position(mousePos.x,mousePos.y)

press_button("Uno") # untested code

def testing(arg):
    print("Hi", arg)

intention_to_function = {
    "move_screens": testing,
    "press_button": testing
}


win_x:int = 0 # Window x pos
win_y:int = 0 # Window y pos

# Get window position
def get_window():
    """
    Gets the current position of the pyglet window
    """
    global win_x, win_y
    
    win_x, win_y, _, _ = ui.window_stats

# Algorithm to interpret user intention
def interpret_intentions(command: str):
    for intention in intention_json:
        for trigger in intention["triggers"]:
            res = extract_placeholder(command, trigger, placeholder="XXX")
            if extract_placeholder(command, trigger, placeholder="XXX"):
                intention_to_function[intention["intention_type"]](res)
                return
            
    # If algorithm fails, use ML
    interpret_intentions_ml()


# Cross-checks a string from a template - if they match, return the value
# of what was labeled by a placeholder
def extract_placeholder(text, template, placeholder="XXX"):
    # Build regex from template
    regex = re.escape(template).replace(re.escape(placeholder), r"(.+)")
    
    # Try to match entire string
    reg_match = re.fullmatch(regex, text, flags=re.IGNORECASE)
    
    # Only return value if pattern fully matches
    if not reg_match:
        return None
    
    return reg_match.group(1).strip()

def interpret_intentions_ml():
    pass




# TODO: 
# Have audio recorder language be customizable (likely with some config file created on software installation)