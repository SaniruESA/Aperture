"""
A way to interact with the server via a client in an easier manner for sending data
All functions will return the servers response
"""
from .. import server
from ..logger.basic_logs import *
import json
from .. import settings

CLIENT:server.Client = None

def generate_client(port:int=8080,ip=server.DEFAULT_COMPUTER_IP) -> server.Client:
    """
    Generates a client for use
    """
    global CLIENT
    
    # Generate
    CLIENT = server.Client(port=port,ip=ip)
    
    # Verify
    CLIENT.verify()
    
    # Wait for response
    info(CLIENT.recv(),__name__)
    
    return CLIENT
    
def generate_tts(text:str="",voice:str="en-US-EmmaMultilingualNeural",rate:int=0,volume:int=0,pitch:int=0,priority:int=0) -> str:
    """
    Generates TTS through the server
    
    Arguments:
        text: The text for TTS to say
        voice: The voice for the AI to use (you can find at https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462)
        rate: The additional speed of the voice (%) this can be positive or negative
        volume: The additional volume of the voice (%) this can be positive or negative
        pitch: The additional pitch of the voice (Hz) this can be positive or negative
        priority: The urgency of the audio to be played (lower will be played first)
    """
    
    info(f"Sent generation request with text: {text}",__name__)
    
    # Queue generation
    return CLIENT.send_and_recv({"type":"generate_tts","content":text,"voice":voice,"volume":volume,"pitch":pitch,"priority":priority})

def exit() -> str:
    """
    Immediately quits the server
    """
    
    info("Sent quit request to server",__name__)
    
    # Send exit request
    return CLIENT.send_and_recv({"type":"exit"})

def help(func:str="") -> str:
    """
    Gets help on all server functions or a specific one (will return help data)
    
    Argument:
        func:
            Function to get help on (leave blank for list)
    """
    
    info(f"Getting help on: {func}",__name__)
    
    # Get help
    return CLIENT.send_and_recv({"type":"help","content":func})
    
def add_button(position:list[int,int,int,int],name:str) -> str:
    """
    Generates a button on the server side for both selection and hover tts
    
    Arguments:
        position:
            The position expressed as a list of [x,y,w,h]
        name:
            The name of the button (this will be played on hover or tab select)
    """

    info(f"Adding button at: {position} with text: {name}",__name__)
    
    return CLIENT.send_and_recv({"type":"add_button","content":json.dumps(position),"name":name})

def clear_button() -> str:
    """
    Clears all and ui elements on the screen
    """

    info("Clearing all buttons",__name__)
    
    return CLIENT.send_and_recv({"type":"clear_button"})

def update_window(position:list[int,int,int,int]) -> str:
    """
    Updates the position of the window and button placement
    It is ideal to do this on window generation and every window update in order to keep objects correctly placed
    
    Arguments:
        position: 
            The window position as a rect [x,y,w,h]
    """
    
    info(f"Setting window position to: {position}",__name__)
    
    return CLIENT.send_and_recv({"type":"update_window","content":json.dumps(position)})

def add_popup(text:str,background_color:tuple[int,int,int]=settings.POPUP_DEFAULT_COLOR,text_color:tuple[int,int,int]=(0,0,0),position:tuple[int,int]=None) -> str:
    """
    Adds a popup to the screen with tts as well
    
    Arguments:
        text:
            The text of the popup
        background_color:
            The background color of the popup
        text_color:
            The text color of the popup
        position:
            The bottom left position of the popup, or none if it is in the popups list
    """
    
    info(f"Adding popup: {text}",__name__)
    
    return CLIENT.send_and_recv({"type":"add_popup","content":text,"text-color":text_color,"background-color":background_color,"position":position})