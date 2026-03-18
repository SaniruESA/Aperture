"""
A basic server to connect python and other languages together
"""

import socket
from typing import Literal
from ..logger.basic_logs import warn, info, error, critical
import os
import json
from ..tts import Queue
import keyboard
from vosk import KaldiRecognizer, Model
import pyaudio
import threading

p = pyaudio.PyAudio()

possible_server_types = Literal[
    socket.SOCK_STREAM, socket.SOCK_DGRAM
]  # Possible socket types
DEFAULT_COMPUTER_IP = socket.gethostbyname(
    socket.gethostname()
)  # The machine ip of the running system


def generic_recv(sock: socket.socket):

    # Read and decode

    # Form header
    header = ""
    while "\n" not in header:
        header += sock.recv(1).decode()

        if header == "":
            raise Exception("Bad read")
    header = header[:-1]

    # Get remaining data
    remaining = int(header)
    data = sock.recv(remaining)

    # Return with removed header
    return data


def generic_send(sock: socket.socket, data: str):

    # Find length header
    length = len(data)

    # Encode and send
    sock.send(f"{length}\n{data}".encode())


class Server:

    server_socket: socket.socket
    port: int
    family: socket.AddressFamily
    ip: int
    tts_queue: Queue
    is_alive: bool = True
    model: Model = Model("vosk_listener")
    recognizer: KaldiRecognizer = KaldiRecognizer(model, 160000)
    
    # Make an audio stream for all servers
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=160000,
        input=True,
        frames_per_buffer=8192,
    )

    def __init__(
        self,
        port: int = 8080,
        ip: str = DEFAULT_COMPUTER_IP,
        family: socket.AddressFamily = socket.AF_INET,
    ):
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

        # Save chosen inputs
        self.port = port
        self.ip = ip
        self.family = family
        
        # Begin audio stream
        if self.stream.is_active():
            self.stream.start_stream()

        # Generate server
        try:
            self.server_socket = socket.create_server((ip, port), family=family)
        except Exception:
            critical("Do not try to make multiple servers on the same port", __name__)
            os._exit(0)

        # Print output message
        info(f"Server created at ip: {ip} and port: {port}", __name__)

        # Generate text-to-speech queue
        self.tts_queue = Queue()

        # Generate a keyboard tab navigation
        self.keyboardtab = keyboard_nav.TabNavOrder()

        # Generate a audio transcription stream display
        self.transcription = audio_transcription

        # Add keyboard button shortcuts
        keyboard.add_hotkey("tab", self.keyboardtab.handleTabPress, (False,))
        keyboard.add_hotkey("shift+tab", self.keyboardtab.handleTabPress, (True,))
        keyboard.add_hotkey("enter", self.keyboardtab.handleEnterPress)

        # Clear previous tts files
        self.tts_queue.wipe_dir()

    def accept(self) -> None:
        """
        Accepts the client connection and starts verification
        """

        # Notify that connection is wait
        info("Server waiting for accept", __name__)

        # Accept connection
        client_conn, client_addr = self.server_socket.accept()

        # Print output message
        info(f"Server started connection to {client_addr}", __name__)

        # Start thread
        tick_async_thread = threading.Thread(
            target=server_ticker._tick_server_threaded,
            args=(self, client_conn),
            daemon=True,
        )
        tick_async_thread.start()

    def send(self, data: str, conn: socket.socket) -> None:
        """
        Sends data to server with automatic length header

        Arguments:
            data:
                Data to send to server
        """

        generic_send(conn, data)

    def recv(self, conn: socket.socket) -> str:
        """
        Receives data from server

        Arguments:
            conn:
                Socket to recv from
        """

        try:

            return generic_recv(conn)

        except ValueError as e:

            # Warn about data
            error(f"Corrupted recv data: {e}", __name__)

            # Return blank
            return '{"type":"ERROR","content":"CORRUPT DATA"}'

        except Exception:

            # Print output message
            critical(
                "Client has closed connection unexpectedly, ending server", __name__
            )

            # Kill server
            self.is_alive = False

            # Stop STT
            self.recorder.stop()
            self.recorder.abort()

            # Stop keyboard
            keyboard.clear_all_hotkeys()

            # End
            while not audio_transcription.process.poll():
                audio_transcription.process.terminate()
            os._exit(0)

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

    def get_said(self):

        said_text = ""
        
        while not said_text:
            data = self.stream.read(4096, exception_on_overflow=False)

            # Read data
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                said_text = result["text"]
            
        return said_text


class Client:

    client_socket: socket.socket
    port: int
    family: socket.AddressFamily
    ip: int

    def __init__(
        self,
        port: int = 8080,
        ip: str = DEFAULT_COMPUTER_IP,
        family: socket.AddressFamily = socket.AF_INET,
    ):
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
            self.client_socket = socket.create_connection((ip, port))
        except Exception:
            critical(
                "Please make sure to start the server before running the client",
                __name__,
            )

            os._exit(0)

        # Print output message
        info(f"Client created at ip: {ip} and port: {port}", __name__)

    def connect(self):
        """
        Attempt to start connection to server
        """

        # Connect to server
        self.client_socket.connect((self.ip, self.port))

        # Print output message
        info(f"Client connected at ip: {self.ip} and port: {self.port}", __name__)

    def send(self, data: str):
        """
        Sends data to server with automatic length header

        Arguments:
            data:
                Data to send to server
        """

        generic_send(self.client_socket, data)

    def send_json(self, data: dict):
        """
        Sends json to server with automatic length header

        Arguments:
            data:
                Data to send to server
        """

        # Dump and send
        self.send(json.dumps(data))

    def send_and_recv(self, data: dict) -> str:
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

    def recv(self):
        """
        Receives data from server
        """

        try:
            return generic_recv(self.client_socket)

        except ValueError as e:

            # Warn about data
            error(f"Corrupted recv data: {e}", __name__)

            # Return blank
            return '{"type":"ERROR","content":"CORRUPT DATA"}'

        except Exception:

            # Print output message
            critical(
                "Server has closed connection unexpectedly, quitting program", __name__
            )

            os._exit(0)

    def __str__(self):

        return f"# -- Client -- #\nIP: {self.ip}\nPort: {self.port}\nSocket: {self.client_socket}"

    def disconnect(self):

        # Send close packet
        self.send('{"type":"exit"}')

        # Close socket
        self.client_socket.close()

        # Print output message
        warn("Client closed", __name__)


# Import ticker method and keyboard nav to prevent circular imports
from . import server_ticker as server_ticker
from .. import keyboard_nav
from .. import audio_transcription


def accept_thread(server: Server):
    """
    Constantly checks for new clients

    Arguments:
        server:
            The server to accept on
    """

    # Accept forever
    while True:
        server.accept()


# Method to easily start the server
def fast_start(port: int = 8080, ip: str = DEFAULT_COMPUTER_IP):
    """
    Generates a server, waits for client accept, and starts ticking
    """

    # Generate server
    new_server = Server(port=port, ip=ip)

    # Accept client thread
    threading.Thread(target=accept_thread, args=(new_server,), daemon=True).start()

    # Start audio
    audio_transcription.start_process()

    # Start threading
    new_server.tick_threaded()
    new_server.tick_pyglet()
