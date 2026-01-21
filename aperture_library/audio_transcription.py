import subprocess
import platform
import os

# determine the executable to use based on user os
match platform.system():
    case "Windows":
        exe_path = "aperture_library/audio_transcription_tools/Aperture.exe"
    case "Linux":
        exe_path = "aperture_library/audio_transcription_tools/Aperture"
    case "Darwin":
        exe_path = "aperture_library/audio_transcription_tools/Aperture"

os.chmod(exe_path, 0o755)

process = subprocess.Popen(
    [exe_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

while True:
    # reading 1 chunk at a time
    subtitle_chunk = ""

    byte_chunk = b""
    while byte_chunk != b"\n":
        byte_chunk = process.stdout.read(1)
        subtitle_chunk += byte_chunk.decode('utf-8')
    
    # see if process is finished
    if not byte_chunk:
        break
    
    print(f"Received: {subtitle_chunk}")  # Prints immediately (test)

# Wait for process to complete
process.wait()



class Queue:
    def __init__(self):
        self.queue_text = []
        self.queue_times = []
        self.subtitle_expiry = 3000 #ms

    def add_subtitle(self, content):
        self.queue_text.append(content)
        self.queue_times.append(self.subtitle_expiry)

    def tick(self, tick_time):
        self.queue_times = [t - tick_time for t in self.queue_times]

        start_at = -1

        for e, i in enumerate(self.queue_times):
            if e > 0:
                start_at = i
                break

        if start_at != -1:
            self.queue_times = self.queue_times[start_at:]
            self.queue_text = self.queue_text[start_at:]
            



            
# # testing purposes
# if __name__ == "__main__":
#     run_periodic_task()