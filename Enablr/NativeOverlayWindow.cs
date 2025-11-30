using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Windows.Foundation.Metadata;

namespace TSA_Working_Name
{
    [Deprecated("Not used", default, default)]
    internal sealed class NativeOverlayWindow : IDisposable
    {
        private const string WindowClassName = "NativeSubtitleOverlayWindow";
        private IntPtr _hwnd = IntPtr.Zero;
        private IntPtr _hInstance;
        private string _currentText = string.Empty;
        private readonly object _lock = new();
        private int _screenW;
        private int _screenH;
        private WndProcDelegate? _wndProc;
        private bool _disposed;

        public NativeOverlayWindow()
        {
            _hInstance = GetModuleHandle(null);
            RegisterClass();
            InitPrimaryScreen();
            CreateWindow();
        }

        public void UpdateText(string text, bool isFinal)
        {
            lock (_lock) _currentText = text ?? string.Empty;
            Redraw();
        }

        private void InitPrimaryScreen()
        {
            _screenW = GetSystemMetrics(SM_CXSCREEN);
            _screenH = GetSystemMetrics(SM_CYSCREEN);
        }

        private void RegisterClass()
        {
            _wndProc = new WndProcDelegate(WndProc);
            WNDCLASSEX wc = new()
            {
                cbSize = (uint)Marshal.SizeOf<WNDCLASSEX>(),
                style = 0,
                lpfnWndProc = Marshal.GetFunctionPointerForDelegate(_wndProc),
                cbClsExtra = 0,
                cbWndExtra = 0,
                hInstance = _hInstance,
                hIcon = IntPtr.Zero,
                hCursor = IntPtr.Zero,
                hbrBackground = IntPtr.Zero,
                lpszMenuName = null,
                lpszClassName = WindowClassName,
                hIconSm = IntPtr.Zero
            };
            RegisterClassEx(ref wc);
        }

        private void CreateWindow()
        {
            const int WS_POPUP = unchecked((int)0x80000000);
            const int WS_VISIBLE = 0x10000000;
            const int WS_EX_LAYERED = 0x00080000;
            const int WS_EX_TOPMOST = 0x00000008;
            const int WS_EX_NOACTIVATE = 0x08000000;

            int exStyle = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_NOACTIVATE;
            // Create small initial window; we'll resize in Redraw to content
            _hwnd = CreateWindowEx(exStyle, WindowClassName, string.Empty, WS_POPUP | WS_VISIBLE, 0, 0, 10, 10, IntPtr.Zero, IntPtr.Zero, _hInstance, IntPtr.Zero);
        }

        private void Redraw()
        {
            if (_hwnd == IntPtr.Zero) return;

            string text;
            lock (_lock) text = _currentText;

            int padX = 24; int padY = 16; int maxWidth = Math.Min(_screenW - padX * 2, 1200);
            IntPtr screenDC = GetDC(IntPtr.Zero);
            IntPtr memDC = CreateCompatibleDC(screenDC);

            RECT calcRect = new() { left = 0, top = 0, right = Math.Max(1, maxWidth), bottom = 600 };
            int flags = DT_WORDBREAK | DT_CALCRECT | DT_NOPREFIX;
            if (!string.IsNullOrWhiteSpace(text)) DrawText(memDC, text, text.Length, ref calcRect, flags);
            int textW = Math.Max(1, calcRect.right - calcRect.left);
            int textH = Math.Max(1, calcRect.bottom - calcRect.top);
            int boxW = textW + padX * 2;
            int boxH = textH + padY * 2;
            int boxX = (_screenW - boxW) / 2;
            int boxY = _screenH - boxH - 80;

            BITMAPINFO bmi = new()
            {
                biSize = Marshal.SizeOf<BITMAPINFO>(),
                biWidth = boxW,
                biHeight = -boxH,
                biPlanes = 1,
                biBitCount = 32,
                biCompression = BI_RGB
            };
            IntPtr bitsPtr;
            IntPtr dib = CreateDIBSection(screenDC, ref bmi, DIB_RGB_COLORS, out bitsPtr, IntPtr.Zero, 0);
            if (dib == IntPtr.Zero)
            {
                DeleteDC(memDC);
                ReleaseDC(IntPtr.Zero, screenDC);
                return;
            }
            IntPtr old = SelectObject(memDC, dib);

            int totalBytes = boxW * boxH * 4;
            byte[] fill = new byte[totalBytes];
            for (int i = 0; i < totalBytes; i += 4)
            { fill[i] = 0; fill[i + 1] = 0; fill[i + 2] = 0; fill[i + 3] = 255; }
            Marshal.Copy(fill, 0, bitsPtr, totalBytes);

            if (!string.IsNullOrWhiteSpace(text))
            {
                SetBkMode(memDC, 1);
                SetTextColor(memDC, unchecked((int)0x00FFFFFF));
                RECT textRect = new() { left = padX, top = padY, right = boxW - padX, bottom = boxH - padY };
                DrawText(memDC, text, text.Length, ref textRect, DT_WORDBREAK | DT_NOPREFIX);
                for (int y = textRect.top; y < textRect.bottom; y++)
                {
                    int lineOffset = y * boxW * 4;
                    for (int x = textRect.left; x < textRect.right; x++)
                    {
                        int p = lineOffset + x * 4;
                        if ((Marshal.ReadByte(bitsPtr, p) | Marshal.ReadByte(bitsPtr, p + 1) | Marshal.ReadByte(bitsPtr, p + 2)) != 0)
                            Marshal.WriteByte(bitsPtr, p + 3, 255);
                    }
                }
            }

            POINT ptSrc = new() { x = 0, y = 0 };
            POINT ptDst = new() { x = boxX, y = boxY };
            SIZE size = new() { cx = boxW, cy = boxH };
            BLENDFUNCTION blend = new() { BlendOp = AC_SRC_OVER, BlendFlags = 0, SourceConstantAlpha = 255, AlphaFormat = AC_SRC_ALPHA };
            UpdateLayeredWindow(_hwnd, screenDC, ref ptDst, ref size, memDC, ref ptSrc, 0, ref blend, ULW_ALPHA);

            SelectObject(memDC, old);
            DeleteObject(dib);
            DeleteDC(memDC);
            ReleaseDC(IntPtr.Zero, screenDC);
        }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;
            if (_hwnd != IntPtr.Zero)
            {
                DestroyWindow(_hwnd);
                _hwnd = IntPtr.Zero;
            }
        }

        #region Win32
        [UnmanagedFunctionPointer(CallingConvention.Winapi)] private delegate IntPtr WndProcDelegate(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
        private IntPtr WndProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam)
        {
            const uint WM_DESTROY = 0x0002;
            if (msg == WM_DESTROY) PostQuitMessage(0);
            return DefWindowProc(hWnd, msg, wParam, lParam);
        }

        [StructLayout(LayoutKind.Sequential)] private struct WNDCLASSEX { public uint cbSize; public uint style; public IntPtr lpfnWndProc; public int cbClsExtra; public int cbWndExtra; public IntPtr hInstance; public IntPtr hIcon; public IntPtr hCursor; public IntPtr hbrBackground; [MarshalAs(UnmanagedType.LPWStr)] public string? lpszMenuName; [MarshalAs(UnmanagedType.LPWStr)] public string? lpszClassName; public IntPtr hIconSm; }
        [StructLayout(LayoutKind.Sequential)] private struct RECT { public int left, top, right, bottom; }
        [StructLayout(LayoutKind.Sequential)] private struct POINT { public int x, y; }
        [StructLayout(LayoutKind.Sequential)] private struct SIZE { public int cx, cy; }
        [StructLayout(LayoutKind.Sequential)] private struct BLENDFUNCTION { public byte BlendOp; public byte BlendFlags; public byte SourceConstantAlpha; public byte AlphaFormat; }
        [StructLayout(LayoutKind.Sequential)] private struct BITMAPINFO { public int biSize; public int biWidth; public int biHeight; public short biPlanes; public short biBitCount; public int biCompression; public int biSizeImage; public int biXPelsPerMeter; public int biYPelsPerMeter; public int biClrUsed; public int biClrImportant; }

        private const int BI_RGB = 0;
        private const int DIB_RGB_COLORS = 0;
        private const byte AC_SRC_OVER = 0x00;
        private const byte AC_SRC_ALPHA = 0x01;
        private const int ULW_ALPHA = 0x00000002;
        private const int SM_CXSCREEN = 0; private const int SM_CYSCREEN = 1;
        private const int DT_WORDBREAK = 0x0010; private const int DT_CALCRECT = 0x0400; private const int DT_NOPREFIX = 0x800;
        private const int IDC_ARROW = 32512;

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr GetModuleHandle(string? lpModuleName);
        [DllImport("user32.dll", SetLastError = true)] private static extern IntPtr CreateWindowEx(int dwExStyle, string lpClassName, string lpWindowName, int dwStyle, int X, int Y, int nWidth, int nHeight, IntPtr hWndParent, IntPtr hMenu, IntPtr hInstance, IntPtr lpParam);
        [DllImport("user32.dll", SetLastError = true)] private static extern bool DestroyWindow(IntPtr hWnd);
        [DllImport("user32.dll")] private static extern int GetSystemMetrics(int nIndex);
        [DllImport("user32.dll", SetLastError = true)] private static extern int RegisterClassEx(ref WNDCLASSEX lpwcx);
        [DllImport("user32.dll")] private static extern IntPtr DefWindowProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
        [DllImport("user32.dll")] private static extern void PostQuitMessage(int nExitCode);
        [DllImport("user32.dll", SetLastError = true)] private static extern bool UpdateLayeredWindow(IntPtr hWnd, IntPtr hdcDst, ref POINT pptDst, ref SIZE psize, IntPtr hdcSrc, ref POINT pptSrc, int crKey, ref BLENDFUNCTION pblend, int dwFlags);
        [DllImport("gdi32.dll")] private static extern IntPtr CreateCompatibleDC(IntPtr hdc);
        [DllImport("gdi32.dll")] private static extern bool DeleteDC(IntPtr hdc);
        [DllImport("gdi32.dll")] private static extern IntPtr SelectObject(IntPtr hdc, IntPtr h);
        [DllImport("gdi32.dll")] private static extern bool DeleteObject(IntPtr ho);
        [DllImport("gdi32.dll")] private static extern IntPtr CreateDIBSection(IntPtr hdc, ref BITMAPINFO bmi, int usage, out IntPtr bits, IntPtr hSection, int dwOffset);
        [DllImport("user32.dll")] private static extern IntPtr GetDC(IntPtr hWnd);
        [DllImport("user32.dll")] private static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int DrawText(IntPtr hdc, string lpchText, int cchText, ref RECT lprc, int format);
        [DllImport("gdi32.dll")] private static extern int SetBkMode(IntPtr hdc, int mode);
        [DllImport("gdi32.dll")] private static extern int SetTextColor(IntPtr hdc, int colorRef);
        #endregion
    }
}
