using System;
using System.Diagnostics;
using Whisper.net;
using System.IO;
using TSA_Working_Name;
public class WhisperManager
{
    static WhisperManager()
    {
        WF = null;
    }
    private static WhisperFactory? WF { get; set; }

    public static void LoadModel(string modelPath)
    {
        try
        {
            if (WF != null)
            {
                WF.Dispose();
                WF = null;
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Error disposing previous WhisperFactory: {ex.Message}");
            return;
        }
        
        try
        {
            WF = WhisperFactory.FromPath("C:\\Users\\nicfa\\Downloads\\ggml-tiny.en.bin");
            var process = WF.CreateBuilder().WithLanguage("en").Build();
        }
        catch(WhisperModelLoadException)
        {
            Debug.WriteLine($"Model {modelPath} does not exist!");
            WF.Dispose();
            return;
        }
            

        Debug.WriteLine($"Model {modelPath} loaded sucessfully");
    }

    public static async void Transcribe(Stream audioData)
    {
        if (WF == null)
        {
            Debug.WriteLine("Whisper model not loaded!");
        }
        using var process = WF.CreateBuilder().WithLanguage("en").Build();
        await foreach (var segment in process.ProcessAsync(audioData))
        {
            Console.WriteLine($"{segment.Start}->{segment.End}: {segment.Text}");
        }
    }


}
