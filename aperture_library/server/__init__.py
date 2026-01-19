"""
A basic server to connect python and other languages together
"""

import socket
from typing import Literal
from ..logger.basic_logs import *
import random
import json
from ..tts import Queue
import keyboard
import pyglet
from RealtimeSTT import AudioToTextRecorder
from .. import settings

possible_server_types = Literal[socket.SOCK_STREAM,socket.SOCK_DGRAM] # Possible socket types
DEFAULT_COMPUTER_IP = socket.gethostbyname(socket.gethostname()) # The machine ip of the running system

def solve_verify_code(verify_code:int):
    """
    Does math on verify code to make sure client and server modify code in the same way
    
    Argument:
        verify_code:
            Starting verify code
    """
    
    # Do math
    return int(((verify_code/2)*3)**2)
    
class Server:
    
    server_socket:socket.socket
    port:int
    family:socket.AddressFamily
    ip:int
    client_addr:str
    client_conn:socket.socket
    client_verified:bool = False
    tts_queue:Queue
    is_alive:bool = True
    recorder:AudioToTextRecorder
    
    def __init__(self,port:int=8080,ip:str=DEFAULT_COMPUTER_IP,family:socket.AddressFamily=socket.AF_INET):
        """
        Generates a new server to send and receive requests from the client
        
        It is important to sync the port, ip, and family to be the same as the client
        
        Arguments:
            port:
                The port to run on
            ip:
                The ip to run on
            family:
                The address family to use (this shouldn't be changed)
        """
        
        # Generate recorder (this restarts program)
        self.recorder = AudioToTextRecorder(language=settings.LANGUAGE,spinner=False)

        # Save chosen inputs
        self.port = port
        self.ip = ip
        self.family = family
        
        # Generate server
        try:
            self.server_socket = socket.create_server((ip,port),family=family)
        except:
            critical("Do not try to make multiple servers on the same port",__name__)
            quit()

        # Print output message  
        info(f"Server created at ip: {ip} and port: {port}",__name__)
        
        # Generate text-to-speech queue
        self.tts_queue = Queue()
        
        # Generate a keyboard tab navigation
        self.keyboardtab = keyboard_nav.TabNavOrder()

        # Generate a audio transcription stream display
        self.transcription = audio_transcription
        
        # Add keyboard button shortcuts
        keyboard.add_hotkey("tab",self.keyboardtab.handleTabPress,(False,))
        keyboard.add_hotkey("shift+tab",self.keyboardtab.handleTabPress,(True,))
        keyboard.add_hotkey("enter",self.keyboardtab.handleEnterPress)
        
        # Clear previous tts files
        self.tts_queue.wipe_dir()
        
    def accept(self) -> None:
        """
        Accepts the client connection and starts verification
        """
        
        # Notify that connection is wait
        info("SERVER IS READY",__name__)
        
        # Accept connection
        self.client_conn,self.client_addr = self.server_socket.accept()
        
        # Generate verify code
        self.verify_code = random.randint(0,10000)
        self.verify_code_solved = solve_verify_code(self.verify_code)
        
        # Send connection verification
        self.send('{"type":"verify","content":'+str(self.verify_code)+'}')
        
        # Print output message
        info(f"Server started connection to {self.client_addr} and started verify ({self.verify_code_solved})",__name__)
        
    def send(self,data:str) -> None:
        """
        Sends data to server with automatic length header
        
        Arguments:
            data:
                Data to send to server
        """
        
        # Find length header
        length = len(data)
        
        # Encode and send
        self.client_conn.send(f"{length}\n{data}".encode())
        
    def recv(self,bufsize:int=1024) -> str:
        """
        Receives data from server
        
        Arguments:
            bufsize:
                Maximum amount of data to receive (This is overridden by length header)
        """
        
        try:
            # Read and decode
            data = self.client_conn.recv(bufsize).decode()
            split_data = data.split("\n")
            
            # Find length header
            header = split_data[0]
            
            # Get remaining data (if applicable)
            remaining = int(header)-bufsize-len(header)
            if remaining > 0:
                split_data.append(self.client_conn.recv())
            
            # Return with removed header
            return "".join(split_data[1:])
                    
        except ValueError as e:
            
            # Warn about data
            error(f"Corrupted recv data: {e}",__name__)
            
            # Return blank
            return '{"type":"ERROR","content":"CORRUPT DATA"}'
            
        except:
            
            # Reset server to default state
            self.client_addr = None
            self.client_conn = None
            self.client_verified = False
            
            # Print output message
            critical("Client has closed connection unexpectedly, ending server",__name__)
            
            # Kill server
            self.is_alive = False
            
            # Stop STT
            self.recorder.stop()
            self.recorder.abort()
            
            # Stop keyboard
            keyboard.clear_all_hotkeys()
            
    
    def __str__(self) -> str:
        
        return f"# -- Server -- #\nIP: {self.ip}\nPort: {self.port}\nSocket: {self.server_socket}"
    
    def tick_server(self) -> None:
        """
        Tick server loop to receive, interpret, and return client requests (this prevents the UI overlay from working)
        """
        
        # Tick server
        server_ticker.tick(self)
        
    def tick_threaded(self) -> None:
        """
        Starts the threaded server
        
        THIS SHOULD ONLY EVER BE RUN ONCE
        """
        
        # Start threaded server
        server_ticker.start_threaded_server(self)
        
    def tick_pyglet(self) -> None:
        """
        Starts the pyglet UI server
        
        THIS WILL MAKE ALL OTHER CODE BENEATH NOT RUN
        """
        
        # Start pyglet
        server_ticker.start_pyglet_server(server=self)

class Client:
    
    client_socket:socket.socket
    port:int
    family:socket.AddressFamily
    ip:int
    
    def __init__(self,port:int=8080,ip:str=DEFAULT_COMPUTER_IP,family:socket.AddressFamily=socket.AF_INET):
        """
        Generates a new client to send and receive requests from the host server
        
        It is important to sync the port, ip, and family to be the same as the server
        
        Arguments:
            port:
                The port to run on
            ip:
                The ip to run on
            family:
                The address family to use (this shouldn't be changed)
        """
        
        # Save chosen inputs
        self.port = port
        self.ip = ip
        self.family = family
        
        # Generate client
        try:
            self.client_socket = socket.create_connection((ip,port))
        except:
            critical("Please make sure to start the server before running the client",__name__)
            raise Exception("Server has not yet been initialized")
        
        # Print output message        
        info(f"Client created at ip: {ip} and port: {port}",__name__)

    def verify(self):
        """
        Verifies client to server after server has accepted
        """
        
        # Receive json and load
        data = self.recv()
        try:
            recv_json:dict = json.loads(data)
        except:
            critical(f"Corrupted recv data:\n{data}",__name__)
            quit()
        
        # Make sure type is correct
        if recv_json["type"] != "verify":
            error(f"Invalid received type ({recv_json['type']})",__name__)
        
        # Convert verify code
        verify_code = recv_json["content"]       
        solved_verify_code = solve_verify_code(verify_code)
        
        # Send back
        self.send('{"type":"verify","content":'+str(solved_verify_code)+'}')
        
        # Print output message
        info(f"Client sent verify request to server ({solved_verify_code})",__name__)
       
  
    def connect(self):
        """
        Attempt to start connection to server
        """
        
        # Connect to server
        self.client_socket.connect((self.ip,self.port))
        
        # Print output message        
        info(f"Client connected at ip: {self.ip} and port: {self.port}",__name__)
        
    def send(self,data:str):
        """
        Sends data to server with automatic length header
        
        Arguments:
            data:
                Data to send to server
        """
        
        # Find length header
        length = len(data)
        
        # Encode and send
        self.client_socket.send(f"{length}\n{data}".encode())
        
    def send_json(self,data:dict):
        """
        Sends json to server with automatic length header
        
        Arguments:
            data:
                Data to send to server
        """
        
        # Dump and send
        self.send(json.dumps(data))
        
    def send_and_recv(self,data:dict) -> str:
        """
        Sends json to server with automatic length header and waits for server response
        
        Arguments:
            data:
                Data to send to server
        """
        
        # Send json data
        self.send_json(data)
        
        # Recv server data
        return self.recv()
        
    def recv(self,bufsize:int=1024):
        """
        Receives data from server
        
        Arguments:
            bufsize:
                Maximum amount of data to receive (This is overridden by length header)
        """
        
        try:
            # Read and decode
            data = self.client_socket.recv(bufsize).decode()
            split_data = data.split("\n")
            
            # Find length header
            header = split_data[0]
            
            # Get remaining data (if applicable)
            remaining = int(header)-bufsize-len(header)
            if remaining > 0:
                split_data.append(self.client_socket.recv())
            
            # Return with removed header
            return "".join(split_data[1:])
        
        except ValueError as e:
            
            # Warn about data
            error(f"Corrupted recv data: {e}",__name__)
            
            # Return blank
            return '{"type":"ERROR","content":"CORRUPT DATA"}'
        
        except:
            
            # Print output message
            critical("Server has closed connection unexpectedly, quitting program",__name__)
            
            # Exit program
            quit()
        
    def __str__(self):
        
        return f"# -- Client -- #\nIP: {self.ip}\nPort: {self.port}\nSocket: {self.client_socket}"

    def disconnect(self):
        
        # Send close packet
        self.send('{"type":"exit"}')
        
        # Close socket
        self.client_socket.close()
        
        # Print output message        
        warn("Client closed",__name__)
        
# Import ticker method and keyboard nav to prevent circular imports
from . import server_ticker as server_ticker
from .. import keyboard_nav
from .. import audio_transcription

# Method to easily start the server
def fast_start(port:int=8080,ip:str=DEFAULT_COMPUTER_IP):
    """
    Generates a server, waits for client accept, and starts ticking
    """
    
    # Generate server
    new_server = Server(port=port,ip=ip)
    
    # Accept client
    new_server.accept()

    # Start threading
    new_server.tick_threaded()
    new_server.tick_pyglet()