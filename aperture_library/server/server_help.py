"""
For help menu returns from the server
"""

from ..server import Server
import socket

# Base help menu
HELP_MENU = """
Server for sending and receiving calls to run accessibility functions (If this list gets cut off, increase the maximum buffer size in recv)

Packet Formatting
JSON_DATA_SIZE
{"type":CONTENT_TYPE,"content":CONTENT,...}

The server will almost always send back the same type that was given to it, unless there is a critical error

# - Specific Functions - #

Help
type: help
content: function to get help on

After verification, send a packet for help with the function name in order to get help on that specific function

# - Functions List - #
help - Help menu
exit - Shutdown server
generate_tts - Send a generation request to queue
add_button - Adds a button for tab navigation
update_window - Updates window position
toggle_subtitle - Toggles subtitles
set_default_voice - Sets default TTS voice
list_voices - Lists all TTS voices
list_buttons - Lists buttons
remove_button - Removes a button
"""

# Help menu for help
HELP_HELP = """
Help
type: help
content: function to get help on

After verification, send a packet for help with the function name in order to get help on that specific function
"""

# Help menu for exit
HELP_EXIT = """
Exit
type: exit
content: none

Stops the server and sends a final data stream back confirming server has been stopped
"""

# Help menu for tts request
HELP_TTS = """
Generate TTS
type: generate_tts
content: tts text
Optional Arguments
voice: The voice for the AI to use (you can find at https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462)
rate: The additional speed of the voice (%) this can be positive or negative
volume: The additional volume of the voice (%) this can be positive or negative
pitch: The additional pitch of the voice (Hz) this can be positive or negative
priority: The urgency of the audio to be played (lower will be played first)

Starts a generate request from the edge servers for given tts text
The text will be played once the playing queue is empty and the message has been generated
"""

# Help menu for adding a button
HELP_ADD_BUTTON = """
Add Button
type: add_button
content: button position list [x,y,w,h]
name: Button name

This will add a button for tab navigation to select
"""

HELP_CLEAR_BUTTON = """
Clear Button
type: clear_button
content: None

This will clear all buttons present on the screen
"""

HELP_UPDATE_WINDOW = """
Update Window
type: update_window
content: window position as a rect [x,y,w,h]

Updates the position of the window and button placement
It is ideal to do this on window generation and every window update in order to keep objects correctly placed
"""

HELP_ADD_POPUP = """
Add Popup
type: add_popup
content: popup text
Optional arguments
text-color: color of the text (r,g,b)
background-color: color of the background (r,g,b)
position: the bottom left position of the popup, or none (x,y)

Adds a popup to the screen with tts as well
The rectangle around it is based on the length of the text, \\n is supported
"""

HELP_SUBTITLE_TOGGLE = """
Toggle Subtitles
type: toggle_subtitles
content: boolean (subtitle state)

Toggles the state of the subtitles
True values enable subtitles, False values disable them
"""

HELP_SET_DEFAULT_VOICE = """
Set Default TTS Voice
type: set_default_voice
content: The voice name

Sets the default voice for TTS
Check the list_voices command for a list of voices
"""

HELP_LIST_VOICES = """
List Voices
type: list_voices 

Lists all voices
"""

HELP_LIST_BUTTONS = """
List Buttons
type: list_buttons

Lists all buttons
"""

HELP_REMOVE_BUTTON = """
Remove Button
type: remove_button
content: The button Aria Text

Removes a single button
"""

def format_json(item: str):
    """
    Formats the item in a json packet

    Arguments:
        item:
            The string without any curly brackets around it
    """

    # Add json to packet
    return '{"type":"help","content:"' + item + '"}'


help_decrypt = {
    "": HELP_MENU,
    "help": HELP_HELP,
    "exit": HELP_EXIT,
    "generate_tts": HELP_TTS,
    "add_button": HELP_ADD_BUTTON,
    "clear_button": HELP_CLEAR_BUTTON,
    "update_window": HELP_UPDATE_WINDOW,
    "add_popup": HELP_ADD_POPUP,
    "toggle_subtitle": HELP_SUBTITLE_TOGGLE,
    "list_voices": HELP_LIST_VOICES,
    "set_default_voice": HELP_SET_DEFAULT_VOICE,
    "list_buttons": HELP_LIST_BUTTONS,
    "remove_button": HELP_REMOVE_BUTTON
}


def help_menu(server: Server, recv_json: dict, conn: socket.socket):
    """
    Sends back help menu from server

    Arguments:
        server:
            Server instance
        recv_json:
            Received json content
    """

    # If they are looking for a specific type
    if "content" in recv_json:

        content = recv_json["content"]

        if content in help_decrypt:
            server.send(help_decrypt[content], conn)
        else:
            server.send(
                format_json(
                    "I don't know what help you are trying to access, send help with no content to view full help menu"
                ),
                conn,
            )

    # If they are looking for anything
    else:

        server.send(HELP_MENU, conn)
