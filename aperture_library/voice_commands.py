from RealtimeSTT import AudioToTextRecorder
import json
from .keyboard_nav import TabNavOrder
import pyautogui
from . import ui
import re
from .server import server_ticker
from .voice_command_intentions import intention_json

win_x:int = 0 # Window x pos
win_y:int = 0 # Window y pos

# Get window position
def get_window():
    """
    Helper to get the current position of the pyglet window
    """
    global win_x, win_y
    
    win_x, win_y, _, _ = ui.window_stats


def press_button(page_name: str):
    """Function to carry out user intention of pressing button/moving pages"""

    # Search for a button w/ given name within UI registry
    all_buttons = server_ticker.SERVER.keyboardtab.getUIElements()["button"]
    page_button = [x for x in all_buttons 
                    if ( page_name.lower() in x["ariaText"].lower() 
                    or x["ariaText"].lower() in page_name.lower() )]

    # Return if none are found
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


# Map user intention to functions defined above
intention_to_function = {
    "move_screens": press_button,
    "press_button": press_button
}

def interpret_intentions(command: str):
    """Interpret user intentions based on their vocal input"""
    # print("COMMAND", command)

    # Search through defined set of intentions
    for intention in intention_json:
        for trigger in intention["triggers"]:
            # Extract "content" of user's request
            res = extract_placeholder(command, trigger, placeholder="XXX")

            # If this "content" exists, carry out the action associated with
            # this intention
            if extract_placeholder(command, trigger, placeholder="XXX"):
                intention_to_function[intention["intention_type"]](res)
                return



def extract_placeholder(text, template, placeholder="XXX"):
    """Cross-checks a string from a template. If they match, return the value
    of what was labeled by a placeholder"""

    # Build regex from template
    regex = re.escape(template).replace(re.escape(placeholder), r"(.+)")
    
    # Try to match entire string
    reg_match = re.fullmatch(regex, text, flags=re.IGNORECASE)
    
    # Only return value if pattern fully matches
    if not reg_match:
        return None
    
    return reg_match.group(1).strip()
