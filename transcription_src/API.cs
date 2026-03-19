
using System;

namespace Aperture
{
    public class API
    {
        private static bool initialized = false;

        public static void Initialize(string path)
        {
            initialized = true;
            WhisperManager.LoadModel(path);
            AudioCapturer.StartCapturer();
        }
        /// <summary>
        /// Entry point of the application.
        /// </summary>
        [MTAThread]
        static void Main(string[] args)
        {
            Initialize("Models\\ggml-tiny.en.bin");
        }
    }
}
