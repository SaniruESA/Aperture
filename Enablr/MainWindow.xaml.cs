using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace TSA_Working_Name
{
    public sealed partial class MainWindow : Window
    {
        private readonly DispatcherQueue _dispatcher;

        public MainWindow()
        {
            InitializeComponent();
            _dispatcher = DispatcherQueue.GetForCurrentThread();
            WhisperManager.SubtitleUpdated += OnSubtitleUpdated;
            Closed += (_, __) => WhisperManager.SubtitleUpdated -= OnSubtitleUpdated;
        }

        private void OnSubtitleUpdated(Transcription tx)
        {
            // Ensure UI updates happen on the UI thread
            _dispatcher.TryEnqueue(() => SetSubtitle(tx.Text));
        }

        public void SetSubtitle(string? text)
        {
            text ??= string.Empty;
            SubtitleOverlay.Text = text;
        }
    }
}
