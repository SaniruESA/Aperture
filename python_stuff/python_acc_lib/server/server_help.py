"""
For help menu returns from the server
"""
from ..server import Server

# Base help menu
HELP_MENU = """
Server for sending and receiving calls to run accessibility functions (If this list gets cut off, increase the maximum buffer size in recv)

Packet Formatting
JSON_DATA_SIZE
{"type":CONTENT_TYPE,"content":CONTENT,...}

The server will almost always send back the same type that was given to it, unless there is a critical error

# - Specific Functions - #
Verify
type: verify
content: solved verification code code

The server will always send the unsolved verification code to the client as soon as it connects
If you are using the python library, simply use client.verify() immediately after connecting
If you are not using the python library, send back a packet with the content of int(((verify_code / 2) * 3) ** 2)

Help
type: help
content: function to get help on

After verification, send a packet for help with the function name in order to get help on that specific function

# - Functions List - #
verify - Verify client
help - Help menu
exit - Shutdown server
generate_tts - Send a generation request to queue
add_button - Adds a button for tab navigation
update_window - Updates window position
"""

# Help menu for verify
HELP_VERIFY = """
Verify
type: verify
content: solved verification code code

The server will always send the unsolved verification code to the client as soon as it connects
If you are using the python library, simply use client.verify() immediately after connecting
If you are not using the python library, send back a packet with the content of int(((verify_code / 2) * 3) ** 2)
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

UPDATE_WINDOW = """
Update Window
type: update_window
content: window position as a rect [x,y,w,h]

Updates the position of the window and button placement
It is ideal to do this on window generation and every window update in order to keep objects correctly placed
"""

def format_json(item:str):
    """
    Formats the item in a json packet
    
    Arguments:
        item:
            The string without any curly brackets around it
    """
    
    # Add json to packet
    return '{"type":"help","content:"'+item+'"}'

def help_menu(server:Server,recv_json:dict):
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
        
        match recv_json["content"]:
            
            # Empty menu
            case "":
                
                server.send(format_json(HELP_MENU))
            
            # Help menu
            case "help":
                
                server.send(format_json(HELP_HELP))
                
            # Verify
            case "verify":
                
                server.send(format_json(HELP_VERIFY))
                
            # Exit
            case "exit":
                
                server.send(format_json(HELP_EXIT))
                
            # TTS Generation
            case "generate_tts":
                
                server.send(format_json(HELP_TTS))
                
            # Adding Button
            case "add_button":
                
                server.send(format_json(HELP_ADD_BUTTON))
            
            # Updating Window Position
            case "update_window":
                
                server.send(format_json(UPDATE_WINDOW))
                
            # Other
            case _:
                
                server.send(format_json("I don't know what help you are trying to access, send help with no content to view full help menu"))
    
    # If they are looking for anything
    else:
        
        server.send(HELP_MENU)