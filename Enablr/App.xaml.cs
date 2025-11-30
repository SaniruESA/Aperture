using System;
using System.Diagnostics;
using System.Runtime.InteropServices; // P/Invoke
using Microsoft.UI.Xaml;
using WinRT.Interop; // WindowNative

namespace TSA_Working_Name
{
    public partial class App : Application
    {
        private Window? _window;
        public readonly string WORKING_DIR = AppDomain.CurrentDomain.BaseDirectory;

        public App()
        {
            InitializeComponent();
            WhisperManager.LoadModel("Models\\ggml-tiny.en.bin");
            AudioCapturer.StartCapturer();
            Debug.WriteLine("Application started");
        }

        protected override void OnLaunched(Microsoft.UI.Xaml.LaunchActivatedEventArgs args)
        {
            _window = new InitWindow();
            _window.Activate();

            // Resize to a smaller demo size
            _window.AppWindow.Resize(new Windows.Graphics.SizeInt32(700, 200));
            _window.Title = "Demo";

            // Set window always on top
            try
            {
                var hwnd = WindowNative.GetWindowHandle(_window);
                SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to set topmost: {ex}");
            }
        }

        // P/Invoke for always-on-top
        private static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
        private const uint SWP_NOSIZE = 0x0001;
        private const uint SWP_NOMOVE = 0x0002;

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    }
}
