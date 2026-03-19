"""
Implements the subprocess thread to execute the compiled audio transcription
code written in C#.

Enables asynchronous audio transcription alongside other Aperture library
features.
"""

import subprocess
import platform
import os
import threading
from . import server
from . import ui

# Determine the executable to use based on user os
match platform.system():
    case "Windows":
        exe_path = "aperture_library/audio_transcription_tools/win-x64/Aperture.exe"
    case "Linux":
        exe_path = "aperture_library/audio_transcription_tools/linux-x64/Aperture"
    case "Darwin":
        exe_path = "aperture_library/audio_transcription_tools/osx-arm64/Aperture"

# Grant access to the file path
os.chmod(exe_path, 0o755)


# Open a subprocess for reading subtitle bytestream
def start_process():
    global process
    process = subprocess.Popen(
        [exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    threading.Thread(target=show_subtitles, daemon=True).start()


def show_subtitles():

    while server.MAIN_SERVER.is_alive:
        # Reading 1 chunk at a time
        subtitle_chunk = ""

        # Read until the end of a line
        byte_chunk = b""
        while byte_chunk != b"\n":
            byte_chunk = process.stdout.read(1)
            subtitle_chunk += byte_chunk.decode("utf-8")

            # Update the subtitle in the UI
            ui.CAPTION_SUB = subtitle_chunk

        # See if process is finished
        if not byte_chunk:
            break
