"""
Secondary server for purposes not directly related to client/server
communication within Aperture Library.
"""

import socket
from . import DEFAULT_COMPUTER_IP, possible_server_types
from ..logger.basic_logs import *
import threading


class Secondary_Server:

    def __init__(
        self,
        port: int = 8080,
        ip: str = DEFAULT_COMPUTER_IP,
        family: socket.AddressFamily = socket.AF_INET,
    ):
        """
        An additional server for alternate functions

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

        # Generate server
        try:
            self.server_socket = socket.create_server((ip, port), family=family)
        except:
            critical("Do not try to make multiple servers on the same port", __name__)
            quit()

        # Print output message
        info(f"Server created at ip: {ip} and port: {port}", __name__)

    def accept(self) -> None:
        """
        Accepts the client connection and starts verification
        """

        # Notify that connection is wait
        info("SERVER IS READY", __name__)

        # Accept connection
        self.client_conn, self.client_addr = self.server_socket.accept()

        # Send connection verification
        self.send("Connected!")

        # Print output message
        info(
            f"Server started connection to {self.client_addr} and started verify ({self.verify_code_solved})",
            __name__,
        )

    def recv(self, buffer: int = 1024) -> bytes:
        """
        Recv data from client

        Arguments:
            buffer:
                The maximum bytes to recv (this is fixed)
        """

        return self.client_conn.recv(buffer)

    def send(self, data: bytes):
        """
        Sends bytes to client

        Argument:
            data:
                Data to send
        """

        return self.client_conn.send(data)

    def bind_conn_loop(self, recv_function, buffer: int = 1024):
        """
        Makes and runs a threaded loop that constantly checks for recv data from the client

        This cannot be stopped

        Arguments:
            recv_function:
                The function that gets run on each recv

                Should be of form

                ```def func_name(recv_data:bytes,server_instance:Secondary_Server): ...
                ```
            buffer:
                The recv buffer
        """

        # Start looper
        info("Bound conn loop function to secondary_server", __name__)
        threading.Thread(
            daemon=True,
            target=self.__conn_looper,
            args=(
                recv_function,
                buffer,
            ),
        ).start()

    def __conn_looper(self, recv_function, buffer):

        while True:
            data = self.recv(buffer)

            recv_function(data, self)
