using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Whisper.net;
public class WhisperManager
{
    public static event Action<Transcription>? SubtitleUpdated;

    static ConcurrentQueue<Transcription> TranscriptionQueue = new();
    static WhisperManager()
    {
        WF = null;
    }

    private static WhisperFactory? WF { get; set; }
    private static readonly SemaphoreSlim _whisperLock = new(1, 1); // To ensure single access to Whisper or something


    public static void LoadModel(string modelPath)
    {
        try
        {
            WF?.Dispose();
            WF = null;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[DBG] Error disposing previous WhisperFactory: {ex.Message}");
            return;
        }

        try
        {
            WF = WhisperFactory.FromPath(Path.GetDirectoryName(System.AppContext.BaseDirectory) + "\\" + modelPath);
            Console.WriteLine(WF == null ? "[DBG] WhisperFactory is null after loading!" : "[DBG] WhisperFactory created successfully.");
        }
        catch (WhisperModelLoadException)
        {
            Console.WriteLine($"Model {Path.GetDirectoryName(System.AppContext.BaseDirectory) + "\\" + modelPath} does not exist!");
            WF?.Dispose();
            WF = null;
            return;
        }

        Console.WriteLine($"[DBG] Model {Path.GetDirectoryName(System.AppContext.BaseDirectory) + "\\" +  modelPath} loaded sucessfully");
    }


    public static async Task Transcribe(Stream audioData, CancellationToken ct = default)
    {
        if (WF == null)
        {
            Console.WriteLine("[DBG] Whisper model not loaded!");
            return;
        }
        if (audioData == null || !audioData.CanRead)
        {
            Console.WriteLine("Unreadable stream");
            throw new NotSupportedException("Provided stream is not readable.");
        }

        // Ensure stream is at beginning
        if (audioData.CanSeek) audioData.Position = 0;
        await _whisperLock.WaitAsync(ct).ConfigureAwait(false);
        try
        {

            await using var process = WF.CreateBuilder()
                                       .WithLanguage("en")
                                       .Build();

            var assembler = new ConfidenceSubtitleAssembler();

            await foreach (var segment in process.ProcessAsync(audioData).WithCancellation(ct).ConfigureAwait(false))
            {
                foreach (var update in assembler.AddSegment(segment.Text, segment.Start, segment.End))
                {
                    // Fire live update event
                    SubtitleUpdated?.Invoke(update);

                    // Only output subtitles text; only enqueue final ones
                    if (update.IsFinal)
                    {
                        TranscriptionQueue.Enqueue(update);
                        //Console.WriteLine(update.Text);
                    }
                }
            }

            // Flush any residual buffered text
            if (assembler.TryFlush(out var last))
            {
                SubtitleUpdated?.Invoke(last);
                if (last.IsFinal)
                {
                    TranscriptionQueue.Enqueue(last);
                    Console.WriteLine(last.Text);
                }
            }
        }
        catch(Exception ex) {
     
            
            Console.WriteLine($"Error {ex}");
        }
        finally
        {
            _whisperLock.Release();
        }
    }

    public static bool TryDequeueTranscription(out Transcription transcription)
        => TranscriptionQueue.TryDequeue(out transcription);

    static float EvaluateConfidence(string text)
    {
        // Simple heuristic: longer, punctuated lines -> higher confidence
        if (string.IsNullOrWhiteSpace(text)) return 0f;
        float len = Math.Min(text.Length, 84) / 84f; // normalize to [0,1]
        float punct = (text.EndsWith('.') || text.EndsWith('!') || text.EndsWith('?')) ? 0.2f : 0f;
        return Math.Clamp(len + punct, 0f, 1f);
    }

    // Confidence-based assembler producing interim updates with a stable Id
    private sealed class ConfidenceSubtitleAssembler
    {
        private const int MaxChars = 84;
        private static readonly TimeSpan MaxDuration = TimeSpan.FromSeconds(5);
        private static readonly TimeSpan MaxGap = TimeSpan.FromMilliseconds(700);
        private const int MinFlushCharsOnPunct = 16;
        private const float FinalThreshold = 0.75f; // when >=, mark as final
        private const float MinorDeltaThreshold = 0.05f; // changes smaller than this won't reset confidence

        private readonly StringBuilder _sb = new();
        private TimeSpan _start = TimeSpan.Zero;
        private TimeSpan _end = TimeSpan.Zero;
        private bool _hasAny = false;
        private Guid _currentId = Guid.Empty;
        private float _stability = 0f; // grows as text stabilizes
        private string _lastText = string.Empty;

        public IEnumerable<Transcription> AddSegment(string text, TimeSpan start, TimeSpan end)
        {
            text ??= string.Empty;
            text = text.Replace('\n', ' ').Replace('\r', ' ').Trim();

            // Gap flush
            if (_hasAny && start - _end > MaxGap)
            {
                if (TryFlush(out var flushed))
                {
                    yield return flushed;
                }
            }

            if (!_hasAny)
            {
                _start = start;
                _end = end;
                _hasAny = true;
                _currentId = Guid.NewGuid();
                _stability = 0f;
                _lastText = string.Empty;
            }

            var tokens = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);

            foreach (var token in tokens)
            {
                var prospectiveLen = (_sb.Length == 0 ? 0 : _sb.Length + 1) + token.Length;
                var prospectiveDur = end - _start;

                if (_sb.Length > 0 && (prospectiveLen > MaxChars || prospectiveDur > MaxDuration))
                {
                    if (TryFlush(out var flushed))
                    {
                        yield return flushed;
                    }
                    _start = start;
                    _end = end;
                    _hasAny = true;
                    _currentId = Guid.NewGuid();
                    _stability = 0f;
                    _lastText = string.Empty;
                }

                if (_sb.Length > 0) _sb.Append(' ');
                _sb.Append(token);
                _end = end;

                
                var currentText = _sb.ToString();
                float delta = TextDeltaRatio(_lastText, currentText);
                if (delta <= MinorDeltaThreshold)
                {
                    _stability = Math.Clamp(_stability + 0.1f, 0f, 1f);
                }
                else
                {
                    _stability = Math.Clamp(_stability - delta * 0.3f, 0f, 1f);
                }
                _lastText = currentText;

                var conf = Math.Clamp(EvaluateConfidence(currentText) * 0.7f + _stability * 0.3f, 0f, 1f);

                yield return new Transcription
                {
                    Id = _currentId,
                    Text = currentText,
                    StartTime = _start,
                    EndTime = _end,
                    Confidence = conf,
                    IsFinal = conf >= FinalThreshold && EndsWithSentencePunctuation(_sb)
                };

                if (EndsWithSentencePunctuation(_sb) && conf >= FinalThreshold && _sb.Length >= MinFlushCharsOnPunct)
                {
                    if (TryFlush(out var finalFlush))
                    {
                        yield return finalFlush;
                    }
                }
            }
        }

        public bool TryFlush(out Transcription transcription)
        {
            if (_sb.Length == 0 || !_hasAny)
            {
                transcription = default;
                return false;
            }

            var text = _sb.ToString().Trim();
            _sb.Clear();

            var conf = Math.Clamp(EvaluateConfidence(text) * 0.7f + _stability * 0.3f, 0f, 1f);

            transcription = new Transcription
            {
                Id = _currentId,
                Text = text,
                StartTime = _start,
                EndTime = _end,
                Confidence = conf,
                IsFinal = true
            };

            _hasAny = false;
            _currentId = Guid.Empty;
            _stability = 0f;
            _lastText = string.Empty;
            return true;
        }

        private static bool EndsWithSentencePunctuation(StringBuilder sb)
        {
            if (sb.Length == 0) return false;
            char c = sb[sb.Length - 1];
            return c == '.' || c == '!' || c == '?';
        }

        private static float TextDeltaRatio(string a, string b)
        {
            if (string.IsNullOrEmpty(a)) return 1f;
            if (a == b) return 0f;
            int common = LongestCommonSubsequenceLength(a, b);
            int maxLen = Math.Max(a.Length, b.Length);
            return 1f - (float)common / Math.Max(1, maxLen);
        }

        private static int LongestCommonSubsequenceLength(string a, string b)
        {
            int n = a.Length, m = b.Length;
            var dp = new int[n + 1, m + 1];
            for (int i = 1; i <= n; i++)
            {
                for (int j = 1; j <= m; j++)
                {
                    if (a[i - 1] == b[j - 1]) dp[i, j] = dp[i - 1, j - 1] + 1;
                    else dp[i, j] = Math.Max(dp[i - 1, j], dp[i, j - 1]);
                }
            }
            return dp[n, m];
        }
    }
}
