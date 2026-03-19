using System;

public struct Transcription
{
    public Guid Id { get; set; }
    public string Text { get; set; }
    public float Confidence { get; set; }
    public TimeSpan StartTime { get; set; }
    public TimeSpan EndTime { get; set; }
    public bool IsFinal { get; set; }

    /// <summary>
    /// Initializes a new Transcription instance with the provided text, confidence, and timing information.
    /// </summary>
    public Transcription(string text, float confidence, TimeSpan startTime, TimeSpan endTime)
    {
        Id = Guid.NewGuid();
        Text = text;
        Confidence = confidence;
        StartTime = startTime;
        EndTime = endTime;
        IsFinal = false;
    }
}
