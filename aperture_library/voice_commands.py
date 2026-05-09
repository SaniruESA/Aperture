"""
Handles user's voice commands and interprets them for
further action on the client-side software (for example,
moving through pages or clicking buttons)

Runs asynchronously with Aperture library to provide live
voice command functionality.
"""

from .keyboard_nav import TabNavOrder
import pyautogui
from . import ui
import re
import difflib
from .server import server_ticker
from .voice_command_intentions import intention_json

win_x: int = 0  # Window x pos
win_y: int = 0  # Window y pos


# Get window position
def get_window():
    """
    Helper to get the current position of the pyglet window
    """
    global win_x, win_y
    win_x, win_y, _, _ = ui.window_stats


def press_button(page_name: str, high_priority_kwds: list[str] = []):
    """Function to carry out user intention of pressing button/moving pages"""

    # Search for a button w/ given name within UI registry
    all_buttons = server_ticker.SERVER.keyboardtab.getUIElements()["button"]
    page_button = [
        x for x in all_buttons
        if (
            page_name.lower() in x["ariaText"].lower()
            or x["ariaText"].lower() in page_name.lower()
        )
    ]

    # Filter so only UI elements matching a high-priority
    # keyword are inclued
    if (high_priority_kwds != []):
        high_priority_kwds = [x.lower() for x in high_priority_kwds]
        page_button = [
            x for x in page_button
            if x["ariaText"].lower() in high_priority_kwds
        ]

    # If no exact matches, try fuzzy-matching ariaText values
    if len(page_button) == 0:
        aria_texts = [x["ariaText"] for x in all_buttons]
        # Use difflib to find a close match for the requested page_name
        matches = difflib.get_close_matches(page_name.lower(), [a.lower() for a in aria_texts], n=1, cutoff=0.6)
        if matches:
            best = matches[0]
            page_button = [x for x in all_buttons if x["ariaText"].lower() == best]

    # Return if none are found
    if len(page_button) == 0:
        return -1

    else:
        # Press the button and return mouse to original location
        get_window()
        mousePos = pyautogui.position()
        rect: list = page_button[0]["rect"]

        pyautogui.click(rect[0] + rect[2] / 2 + win_x, rect[1] + rect[3] / 2 + win_y)
        print(rect[0] + rect[2] / 2 + win_x, rect[1] + rect[3] / 2 + win_y)
        pyautogui.position(mousePos.x, mousePos.y)

        # Return 0 for success
        return 0

def close_page(page_name: str):
    """Function to carry out user intention of closing/exiting pages"""

    # Search for buttons relating to closing the page
    press_button(f"{page_name}", ["close", "dismiss", "leave", "exit"])

def search(to_search: str):
    """Function to carry out user intention of searching (via search bar)"""

    # Find/click on search bar
    press_button("search")

    # Type intention into search bar
    pyautogui.write(to_search)
    pyautogui.press("enter")

def fail():
    server_ticker.SERVER.tts_queue.generate(
        "Sorry, I couldn't understand this."
    )

# Map user intention to functions defined above
intention_to_function = {
                        "move_screens": press_button,
                        "press_button": press_button,
                        "open_menu": press_button,
                        "close_or_dismiss": close_page,
                        "type_input": pyautogui.write,
                        "select_option": press_button,
                        "search": search,
                    }

def interpret_intentions(command: str):
    """Interpret user intentions based on their vocal input"""

    # Search through defined set of intentions
    for intention in intention_json:
        for trigger in intention["triggers"]:

            # Try exact placeholder extraction
            res = extract_placeholder(command, trigger, placeholder="XXX")

            if res is not None:
                intention_to_function[intention["intention_type"]](res)
                return res
            
    # Use difflib and keyword searching if it fails
    words = command.split()
    highest_similarity = 0
    closest_info = []

    for intention in intention_json:
        for kw in intention["keywords"]:
            for word in words:
                similarity = difflib.SequenceMatcher(None, kw.lower(), word.lower()).ratio()
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    closest_info = [intention, kw, word]

    # Find argument in voice command
    if closest_info != []:
        argument = command[command.find(closest_info[2]):].strip().split()
        intention_to_function[closest_info[0]["intention_type"]](argument)
        return argument

    # Send fail message as worst case scenario
    fail()
    return None


def extract_placeholder(text: str, template: str, placeholder: str="XXX"):
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

