"""
A way to interact with the server via a client in an easier manner for sending data
All functions will return the servers response
"""
from .. import server
from ..logger.basic_logs import *
import json

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