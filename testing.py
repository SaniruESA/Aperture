from vosk import Model, KaldiRecognizer
import pyaudio,json

model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model,160000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=160000, input=True,frames_per_buffer=8192)
stream.start_stream()

print("Listening")

while True:
    data = stream.read(4096, exception_on_overflow=False)
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        print("You:", result["text"])