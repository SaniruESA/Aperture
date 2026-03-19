"""
Handles continuous server/client communication + connection
within Aperture Library
"""

from ..server import Server
import json
from ..logger.basic_logs import warn, debug, info, error, critical
from . import server_help
from .. import tts
import threading
import asyncio
from .. import ui
from .. import settings
from ..ui import popup
from .. import voice_commands
from .. import audio_transcription
from .. import live_ui
import socket
import keyboard

BLANK_PACKET_MAXIMUM: int = (
    100  # Number of blank packets received before server will automatically shut off
)
BLANK_PACKET_COUNT: int = 0  # Number of blank packets received
SERVER_ASYNC_THREAD: threading.Thread = None  # Async thread for server
PYGLET_ASYNC_THREAD: threading.Thread = None  # Async thread for pyglet
SERVER: Server = None  # Last used server for tick


def queue_generate_tts(server: Server, recv_json: dict, conn: socket.socket):
    """
    Queues generation of text-to-speech

    Arguments:
        server:
            Server instance
        recv_json:
            Received json content
    """

    # Fix the optional arguments
    default_arguments = {
        "pitch": 0,
        "volume": 0,
        "rate": 0,
        "voice": "en-US-EmmaMultilingualNeural",
        "priority": 0,
    }
    for argument in default_arguments:

        # Add if argument is missing
        if argument not in recv_json:

            recv_json[argument] = default_arguments[argument]

    # Start queue
    server.tts_queue.generate(
        recv_json["content"],
        voice=recv_json["voice"],
        volume=recv_json["volume"],
        pitch=recv_json["pitch"],
        priority=recv_json["priority"],
        rate=recv_json["rate"],
    )

    # Return back
    server.send('{"type":"tts_queue","content":"Started"}', conn)


def generate_button_tts(name: str, path: str):
    """
    Generates TTS for a button to play when hovered

    Arguments:
        name:
            The name of the button
        path:
            The path of the button TTS text
    """

    asyncio.run(tts.generate_no_play(name, path=path))


def add_button(server: Server, recv_json: dict, conn: socket.socket):
    """
    Adds a button to known server buttons for tab nav

    Arguments:
        server:
            Server instance
        recv_json:
            Received json content
    """

    # Get rect
    rect = json.loads(recv_json["content"])
    name = recv_json["name"]

    # Add button to list
    server.keyboardtab.addUIElement(rect, "button", name)

    # Preprocess text
    path = f".\\temp\\output_{name}.mp3"
    threading.Thread(target=generate_button_tts, args=(name, path)).start()

    # Return back
    server.send('{"type":"add_button","content":"Button has been added"}', conn)


def clear_button(server: Server, recv_json: dict, conn: socket.socket):
    """
    Clears all buttons from the server

    Arguments:
        server:
            Server instance
        recv_json:
            Received json content
    """

    # Clear buttons
    server.keyboardtab.clearAllUIElements()

    # Return back
    server.send('{"type":"add_button","content":"All buttons have been removed"}', conn)


def add_missing(base: dict, example: dict):
    """
    Adds any missing keys or values to base from example

    Arguments:
        base:
            The base dictionary (this will be favored for values)
        example:
            The example diction (this will be pulled for values)
    """

    for key in example:

        # Substitute in
        if key not in base:

            base[key] = example[key]

    # Return fixed
    return base


def add_popup(server: Server, recv_json: dict, conn: socket.socket):

    # Add missing keys
    recv_json = add_missing(
        recv_json,
        {
            "text-color": (0, 0, 0),
            "background-color": settings.POPUP_DEFAULT_COLOR,
            "position": None,
        },
    )

    # Add popup
    popup.add_popup(
        {
            "text": recv_json["content"],
            "text-color": recv_json["text-color"],
            "background-color": recv_json["background-color"],
            "position": recv_json["position"],
        }
    )

    # Send back
    server.send('{"type":"add_popup","content":"Added popup"}', conn)


def _server_threaded(server: Server):
    """
    Thread of the server

    Arguments:
        server:
            Server instance
    """

    # Notify that thread was started
    info("Server thread started", __name__)

    # This will run forever until program end
    while server.is_alive:

        # Run tts generation and play check
        server.tts_queue.check_generate()
        server.tts_queue.check_play()
        server.keyboardtab.hoverTTS()

    # Notify that thread was ended
    info("Server thread ended", __name__)


def _tick_server_threaded(server: Server, conn: socket.socket):
    """
    Tick threaded server
    """

    # Notify that thread was started
    info("Started server ticking", __name__)

    # Tick forever
    while server.is_alive:

        tick(server, conn)

        # Notify that thread was ended
    info("Ended server ticking", __name__)


def _voice_command_server_threaded(server: Server):
    """
    Tick voice command server
    """
    # Preprocess listening text
    path = ".\\temp\\voice_assistant_listening.mp3"
    threading.Thread(
        target=generate_button_tts, args=(settings.VOICE_ACTIVATION_CONFIRMATION, path)
    ).start()

    # Notify that thread was started
    info("Started server voice commands", __name__)

    # Tick forever
    while server.is_alive:

        # Get what user said
        said_text = server.get_said()

        # Log what user said
        info("User Said:" + said_text, __name__)

        # Check if keyword
        if settings.VOICE_ACTIVATION_KEYWORD in said_text.lower():

            # Log what user said
            info("Voice assistant activated", __name__)

            # Say that AI is listening
            server.tts_queue.queue_play(
                ".\\temp\\voice_assistant_listening.mp3",
                -1,
                settings.VOICE_ACTIVATION_CONFIRMATION,
                True,
                True,
            )

            # Listen to user text and pipe to AI
            said_text = server.get_said()
            voice_commands.interpret_intentions(said_text.lower())

            # Log what user said
            info("User said to voice assistant:" + said_text, __name__)

    # Notify that thread was ended
    info("Ended server voice commands", __name__)


def start_threaded_server(server: Server):
    """
    Tick server async (for tts generation)

    Arguments:
        server:
            Server instance
    """
    global SERVER_ASYNC_THREAD, SERVER_ASYNC_RUNNING, PYGLET_ASYNC_THREAD, WINDOW, VOICE_ASYNC_THREAD

    # Set running to true to allow thread to run
    SERVER_ASYNC_RUNNING = True

    # Generate and start thread
    SERVER_ASYNC_THREAD = threading.Thread(target=_server_threaded, args=(server,))
    SERVER_ASYNC_THREAD.start()

    VOICE_ASYNC_THREAD = threading.Thread(
        target=_voice_command_server_threaded, args=(server,)
    )
    VOICE_ASYNC_THREAD.start()

    WINDOW = ui.Window(settings.DEFAULT_WINDOW_WIDTH, settings.DEFAULT_WINDOW_HEIGHT)


def tick(server: Server, conn: socket.socket):
    """
    Tick server

    Arguments:
        server:
            Server instance
    """
    # SERVER global variable
    global SERVER
    SERVER = server

    # Receive data
    recv_data: str = server.recv(conn)

    # Stop if data is blank
    if len(recv_data) == 0:

        global BLANK_PACKET_COUNT
        error(
            f"Empty received data ({BLANK_PACKET_COUNT}/{BLANK_PACKET_MAXIMUM})",
            __name__,
        )

        # Increment blank packets by 1
        BLANK_PACKET_COUNT += 1

        # If blank packets have reached maximum stop the server
        if BLANK_PACKET_COUNT >= BLANK_PACKET_MAXIMUM:

            # Send last log
            critical("Maximum number of empty packets, ending server", __name__)

            server.is_alive = False
            quit()

        return

    # Convert data to json
    try:
        recv_json: dict = json.loads(recv_data)
        content_type: str = recv_json["type"]

    # Stop if data is unable to be read
    except Exception:
        error(f"Malformed json data: {recv_data}", __name__)

        # Return back error
        server.send(
            '{"type":"error","content":"Malformed JSON (send "help" for a help menu)"}',
            conn,
        )
        return

    # Log that content was received
    info(f"Received content of type: ({content_type})", __name__)

    # Run different protocol based on type
    match content_type:

        # Exiting
        case "exit":

            # Log message
            info("Client has ended connection, ending server", __name__)

            # Send final output
            server.send('{"type":"close"}', conn)

            # Close
            server.is_alive = False

            # Stop keyboard
            keyboard.clear_all_hotkeys()

            # End
            while not audio_transcription.process.poll():
                audio_transcription.process.terminate()
            quit()

        # TTS Generation
        case "generate_tts":

            # Queue generation
            queue_generate_tts(server, recv_json, conn)

        # Help message
        case "help":

            # Return help menu
            server_help.help_menu(server, recv_json, conn)

        # Adding button
        case "add_button":

            # Add a button to tab nav
            add_button(server, recv_json, conn)

        # Clearing button
        case "clear_button":

            # Remove button from tab nav
            clear_button(server, recv_json, conn)

        # Updating window
        case "update_window":

            # Change window position
            x, y, w, h = json.loads(recv_json["content"])
            info(f"Updating window position x: {x} y: {y} w: {w} h: {h}", __name__)

            # Start update
            ui.update_window = True
            ui.window_stats = [x, y, w, h]

            # Send back
            server.send('{"type":"update_window","content":"Window updated"}', conn)

        # Adding a popup
        case "add_popup":

            add_popup(server, recv_json, conn)

        case "show_transcription":

            audio_transcription.Queue.add_subtitle(recv_json["content"])

            # Send back
            server.send(
                '{"type":"show_transcription","content":"Transcription shown"}', conn
            )

        case "UI_show":

            live_ui.LiveUI.show_element(recv_json["content"])

            # Send back
            server.send('{"type":"UI_show","content":"UI shown"}', conn)

        # Unknown type
        case _:

            # Log message
            error(f"Unknown type: {content_type}", __name__)

            # Return back error
            server.send(
                '{"type":"error","content":"Unknown type (send "help" for a help menu)"}',
                conn,
            )


def start_pyglet_server(server: Server):
    """
    Starts the pyglet portion of the server
    """

    # Start app
    info("Started pylget app", __name__)
    WINDOW.run(server)