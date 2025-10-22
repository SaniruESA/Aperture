"""
Ticker for server.Server
"""
from ..server import Server
import json
from ..logger.basic_logs import *
from .. import tts
from . import server_help
import threading
import atexit

BLANK_PACKET_MAXIMUM:int = 100 # Number of blank packets received before server will automatically shut off
BLANK_PACKET_COUNT:int = 0 # Number of blank packets received
SERVER_ASYNC_THREAD:threading.Thread = None # Async thread for server
    
def verify(server:Server,recv_json:dict):
    """
    Verify protocol for server
    
    Arguments:
        server:
            Server instance
        recv_json:
            Received json content
    """
    
    # Extract code
    recv_code = recv_json["content"]
    
    # Check if code is correct
    if recv_code != server.verify_code_solved:
        warn(f"Received code: {recv_code} is not the same as server code: {server.verify_code_solved}",__name__)
        
        # Send code
        server.send('{"type":"verify","content":"FAILED"}')
        return
    
    # Enable verified state
    server.client_verified = True
    
    # Send code
    server.send('{"type":"verify","content":"PASSED"}')
    
    # Notify that server is ready
    info(f"Server verification passed",__name__)
    
def queue_generate_tts(server:Server,recv_json:dict):
    """
    Queues generation of text-to-speed
    
    Arguments:
        server:
            Server instance
        recv_json:
            Received json content
    """

    # Fix the optional arguments
    default_arguments = {"pitch":0,"volume":0,"rate":0,"voice":"en-US-EmmaMultilingualNeural","priority":0}
    for argument in default_arguments:
        
        # Add if argument is missing
        if argument not in recv_json:
            
            recv_json[argument] = default_arguments[argument]
    
    # Start queue
    server.tts_queue.generate(recv_json["content"],voice=recv_json["voice"],volume=recv_json["volume"],pitch=recv_json["pitch"],priority=recv_json["priority"],rate=recv_json["rate"])
    
    # Return back
    server.send('{"type":"tts_queue","content":"Started"}')

def _server_threaded(server:Server):
    """
    Thread of the server
    
    Arguments:
        server:
            Server instance
    """
    
    # Notify that thread was started
    info("Server thread started",__name__)
    
    # This will run forever until program end
    while server.is_alive:
        
        # Run tts generation and play check
        server.tts_queue.check_generate()
        server.tts_queue.check_play()
        
    # Notify that thread was ended
    info("Server thread ended",__name__)
    
def start_threaded_server(server:Server):
    """
    Tick server async (for tts generation)
    
    Arguments:
        server:
            Server instance
    """
    global SERVER_ASYNC_THREAD,SERVER_ASYNC_RUNNING
    
    # Set running to true to allow thread to run
    SERVER_ASYNC_RUNNING = True
    
    # Generate and start thread
    SERVER_ASYNC_THREAD = threading.Thread(target=_server_threaded,args=(server,))
    SERVER_ASYNC_THREAD.start()
    
def tick(server:Server):
    """
    Tick server
    
    Arguments:
        server:
            Server instance
    """
    
    # Receive data
    recv_data:str = server.recv()
    
    # If content is for help, show help menu and end
    if recv_data.lower() == "help":
        
        server_help.help_menu(server,{})
        return
        
    # Stop if data is blank
    if len(recv_data) == 0:
        
        global BLANK_PACKET_COUNT
        error(f"Empty received data ({BLANK_PACKET_COUNT}/{BLANK_PACKET_MAXIMUM})",__name__)
        
        # Increment blank packets by 1
        BLANK_PACKET_COUNT += 1
        
        # If blank packets have reached maximum stop the server
        if BLANK_PACKET_COUNT >= BLANK_PACKET_MAXIMUM:
            
            # Send last log
            error("Maximum number of empty packets, ending server",__name__)
            
            server.is_alive = False
            quit()
        
        return
    
    # Convert data to json
    try:
        recv_json:dict = json.loads(recv_data)
        content_type:str = recv_json['type']
        
    # Stop if data is unable to be read
    except:
        error(f"Malformed json data: {recv_data}",__name__)
        
        # Return back error
        server.send('{"type":"error","content":"Malformed JSON (send \"help\" for a help menu)"}')
        return
    
    # Log that content was received
    info(f"Received content of type: ({content_type})",__name__)
    
    # If content type is not for verification, and client is unverified, end
    if (not server.client_verified) and content_type != "verify":
        
        error("Client is not yet verified",__name__)
        
        # Return back error
        server.send('{"type":"error","content":"Client not yet verified (send \"help\" for a help menu)"}')
        return
    
    # Run different protocol based on type
    match content_type:
        
        # Verification
        case "verify":
            verify(server,recv_json)
            
        # Exiting
        case "exit":
            
            # Log message
            info("Client has ended connection, ending server",__name__)
            
            # Send final output
            server.send('{"type":"close"}')
            
            # Close
            server.is_alive = False
            quit()
        
        # TTS Generation
        case "generate_tts":
            
            # Queue generation
            queue_generate_tts(server,recv_json)
            
        # Help message
        case "help":
            
            # Return help menu
            server_help.help_menu(server,recv_json)
        
        # Unknown type
        case _:
            
            # Log message
            error(f"Unknown type: {content_type}",__name__)
            
            # Return back error
            server.send('{"type":"error","content":"Unknown type (send \"help\" for a help menu)"}')