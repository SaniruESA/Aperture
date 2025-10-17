using System;
using System.Diagnostics;
using System.Threading.Tasks;
using NAudio.Wave;
using System.IO;
using NAudio.CoreAudioApi;
public class AudioCapturer : IDisposable
{
    public const int StreamTime = 2000;
    static async Task Capturer()
    {
        Debug.WriteLine("Audio capture started");

        var deviceEnum = new MMDeviceEnumerator();
        var device = deviceEnum.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);


        using var capture = new WasapiLoopbackCapture(device);
        var memStream = new System.IO.MemoryStream();

        capture.DataAvailable += (s, a) =>
        {
            memStream.Write(a.Buffer, 0, a.BytesRecorded);

            if (memStream.Length >= capture.WaveFormat.AverageBytesPerSecond * StreamTime / 1000)
            {
                // Process chunk of audio data
                var chunk = new System.IO.MemoryStream(memStream.ToArray());
                Debug.WriteLine($"Captured {chunk.Length} bytes of audio data");
                _ = Task.Run(() => ProcessAudioChunk(chunk));

                memStream.SetLength(0); // Clear the memory stream for the next chunk
                memStream.Position = 0;

            }
        };
        capture.StartRecording();

        for (; ; ) { }
    }

    static async Task ProcessAudioChunk(Stream stream)
    {
        Debug.WriteLine("Audio Processing Placeholder...");
        WhisperManager.Transcribe(stream);
    }

    public async static void StartCapturer()
    {
        Task.Run(() => Capturer());
    }

    public void Dispose() { }
}
