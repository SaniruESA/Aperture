using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System.Diagnostics; 
namespace TSA_Working_Name
{
    public sealed partial class InitWindow : Window
    {

        public InitWindow()
        {
            InitializeComponent();
            var psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"enablr\\python_stuff\\shart.py",
                UseShellExecute = false
            };

            Process.Start(psi);
        }
    }
}
