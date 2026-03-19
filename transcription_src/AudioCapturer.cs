using NAudio.CoreAudioApi;
using NAudio.Wave;
using System;
using System.IO;
using System.Threading.Channels;
using System.Threading.Tasks;

public class AudioCapturer : IDisposable
{

    public const int StreamTime = 1000; // milliseconds
    public static readonly int CacheSize = 5;
    protected static bool alive = false;

    private static readonly WaveFormat TargetFormat = new WaveFormat(16000, 1); // 16 kHz, 16-bit mono

    // Rolling, non-destructive audio cache
    public static readonly RollingPcmBuffer AudioCache;

    static AudioCapturer()
    {
        if (CacheSize > 0)
        {
            AudioCache = new RollingPcmBuffer(TargetFormat.AverageBytesPerSecond * CacheSize);
        }
        else
        {
            AudioCache = new RollingPcmBuffer(1); // unused when CacheSize == 0
        }
    }

    // Single-consumer queue to avoid concurrent Whisper calls
    private static readonly Channel<MemoryStream> _audioQueue =
        Channel.CreateUnbounded<MemoryStream>(new UnboundedChannelOptions
        {
            SingleReader = true,
            AllowSynchronousContinuations = false
        });

    private static readonly Task _consumerTask = Task.Run(ProcessQueueAsync);

    private static async Task ProcessQueueAsync()
    {
        await foreach (var ms in _audioQueue.Reader.ReadAllAsync().ConfigureAwait(false))
        {
            try
            {
                ms.Position = 0;
                await WhisperManager.Transcribe(ms).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DBG] Transcribe error: {ex}");
            }
            finally
            {
                ms.Dispose();
            }
        }
    }

    [MTAThread]
    static async void Capturer()
    {
        try
        {
            var deviceEnum = new MMDeviceEnumerator();
            var device = deviceEnum.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);

            using var capture = new WasapiLoopbackCapture(device);
            var memStream = new MemoryStream();

            capture.DataAvailable += (s, a) =>
            {
                using var inputStream = new RawSourceWaveStream(
                    new MemoryStream(a.Buffer, 0, a.BytesRecorded, false, false),
                    capture.WaveFormat);

                using var resampler = new MediaFoundationResampler(inputStream, TargetFormat)
                {
                    ResamplerQuality = 60
                };

                var buffer = new byte[TargetFormat.AverageBytesPerSecond];
                int bytesRead;
                while ((bytesRead = resampler.Read(buffer, 0, buffer.Length)) > 0)
                {
                    memStream.Write(buffer, 0, bytesRead);
                }

                if (memStream.Length >= TargetFormat.AverageBytesPerSecond * StreamTime / 1000)
                {
                    memStream.Position = 0;

                    // Wrap current PCM chunk into a WAV stream
                    var wavMemStream = new MemoryStream(capacity: (int)memStream.Length + 44);
                    var writer = new WaveFileWriter(wavMemStream, TargetFormat);

                    writer.Write(memStream.GetBuffer(), 0, (int)memStream.Length);
                    writer.Flush();

                    wavMemStream.Position = 0;

                    // Use cached audio
                    if (CacheSize != 0)
                    {
                        //Debug.WriteLine($"The captured audio chunk length: {wavMemStream.Length} bytes");
                        //Debug.WriteLine($"Capacity of AudioCache: {AudioCache.BufferedBytes}/{AudioCache.BufferLength} bytes");

                        // Extract PCM payload from WAV (skip 44-byte header) and add to rolling cache
                        int newPcmBytes = (int)wavMemStream.Length - 44;
                        if (newPcmBytes > 0)
                        {
                            var pcmBuf = new byte[newPcmBytes];
                            wavMemStream.Position = 44;
                            _ = wavMemStream.Read(pcmBuf, 0, newPcmBytes);
                            AudioCache.AddSamples(pcmBuf, 0, newPcmBytes);
                        }

                        // If cache not full, still send the current chunk for transcription
                        if (AudioCache.BufferedBytes < AudioCache.BufferLength)
                        {
                            //Debug.WriteLine("Cache not full yet; sending current chunk for transcription.");

                            if (!_audioQueue.Writer.TryWrite(wavMemStream))
                            {
                                //Debug.WriteLine("Dropping audio chunk; queue not accepting writes.");
                                wavMemStream.Dispose();
                            }

                            memStream.SetLength(0);
                            return;
                        }

                        // Cache is full: send a non-destructive rolling window snapshot (last N seconds)
                        var cacheBuffer = AudioCache.Snapshot();
                        var wavStream = new MemoryStream(capacity: cacheBuffer.Length + 44);
                        var writerr = new WaveFileWriter(wavStream, TargetFormat);

                        writerr.Write(cacheBuffer, 0, cacheBuffer.Length);
                        writerr.Flush();


                        wavStream.Position = 0;
                        //Debug.WriteLine($"Captured {wavStream.Length} bytes of cached audio data (rolling window)");

                        if (!_audioQueue.Writer.TryWrite(wavStream))
                        {
                            //Debug.WriteLine("Dropping cached audio chunk; queue not accepting writes.");
                            wavStream.Dispose();
                        }

                        wavMemStream.Dispose();
                        memStream.SetLength(0);
                        return;
                    }

                    // No cache: send the current chunk
                    //Debug.WriteLine($"Captured {wavMemStream.Length} bytes of audio data");

                    if (!_audioQueue.Writer.TryWrite(wavMemStream))
                    {
                        //Debug.WriteLine("Dropping audio chunk; queue not accepting writes.");
                        wavMemStream.Dispose();
                    }
                    memStream.SetLength(0);
                }
            };

            capture.StartRecording();

            // Keep capture alive
            for (; ; )
            {
                await Task.Delay(500).ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[DBG] Capturer error: {ex}");
        }
    }

    [MTAThread]
    public static void StartCapturer()
    {
        alive = true;
        
        _ = Task.Run(() => Capturer());
        // keep thread alive

        while (alive)
        {
            Task.Delay(1000).Wait();
        }
    }

    public void Dispose() { }

    // Rolling, non-destructive PCM byte buffer with snapshot capability
    public sealed class RollingPcmBuffer
    {
        private readonly byte[] _buffer;
        private int _write;
        private int _size;
        private readonly object _lock = new();

        public RollingPcmBuffer(int capacity)
        {
            if (capacity < 1) capacity = 1;
            _buffer = new byte[capacity];
        }

        public int BufferLength => _buffer.Length;
        public int BufferedBytes => _size;

        public void AddSamples(byte[] src, int offset, int count)
        {
            if (count <= 0) return;

            lock (_lock)
            {
                if (count >= _buffer.Length)
                {
                    // Keep only the last capacity bytes
                    offset = offset + count - _buffer.Length;
                    count = _buffer.Length;
                    Buffer.BlockCopy(src, offset, _buffer, 0, count);
                    _write = 0;
                    _size = count;
                    return;
                }

                int toEnd = _buffer.Length - _write;
                if (count <= toEnd)
                {
                    Buffer.BlockCopy(src, offset, _buffer, _write, count);
                    _write = (_write + count) % _buffer.Length;
                }
                else
                {
                    Buffer.BlockCopy(src, offset, _buffer, _write, toEnd);
                    Buffer.BlockCopy(src, offset + toEnd, _buffer, 0, count - toEnd);
                    _write = count - toEnd;
                }

                _size = Math.Min(_size + count, _buffer.Length);
            }
        }

        public byte[] Snapshot()
        {
            lock (_lock)
            {
                var result = new byte[_size];
                if (_size == 0) return result;

                int start = _write - _size;
                if (start < 0) start += _buffer.Length;

                int first = Math.Min(_buffer.Length - start, _size);
                Buffer.BlockCopy(_buffer, start, result, 0, first);
                if (first < _size)
                {
                    Buffer.BlockCopy(_buffer, 0, result, first, _size - first);
                }
                return result;
            }
        }
    }

    
        
}
