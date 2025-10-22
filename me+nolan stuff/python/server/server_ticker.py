"""
Ticker for server.Server
"""
from python.server import Server
import json
from python.log.basic_logs import *

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
        error(f"Received code: {recv_code} is not the same as server code: {server.verify_code_solved}",__name__)
        
        # Send code
        server.send('{"type":"verify","content":"FAILED"}')
        return
    
    # Enable verified state
    server.client_verified = True
    
    # Send code
    server.send('{"type":"verify","content":"PASSED"}')
    
    # Notify that server is ready
    info(f"Server verification passed\n{server}",__name__)
    
    
def tick(server:Server):
    """
    Tick server
    
    Arguments:
        server:
            Server instance
    """
    
    # Receive data
    recv_data = server.recv()
    
    # Convert data to json
    try:
        recv_json = json.loads(recv_data)
        content_type = recv_json['type']
    except:
        error(f"Malformed json data: {recv_data}",__name__)
        return
    
    # Log that content was received
    info(f"Received content of type: ({content_type})",__name__)
    
    # If content type is not for verification, and client is unverified, end
    if (not server.client_verified) and content_type != "verify":
        error("Client is not yet verified",__name__)
        return
    
    # Run different protocol based on type
    match content_type:
        
        # Verification
        case "verify":
            verify(server,recv_json)
            
        # Exiting
        case "exit":
            
            # Log message
            info("Client has ended connection",__name__)
            
            # Send final output
            server.send('{"type":"close"}')
            
            # Close
            quit()