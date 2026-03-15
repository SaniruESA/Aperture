# Build script for Aperture for Windows
Write-Host "Setting up Virtual Environment" -ForegroundColor Cyan
Set-Location -Path ..
Remove-Item -Path ".venv", "website\dist", "build", "dist", "Aperture.exe.spec" -Recurse -Force -ErrorAction SilentlyContinue

python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
& ".\.venv\Scripts\Activate.ps1"

\Write-Host "Installing Python Dependencies" -ForegroundColor Cyan
python -m pip install --upgrade pip setuptools wheel
pip install PyGithub GitPython requests pyperclip huggingface-hub pyinstaller
pip freeze > requirements.txt

Write-Host "Building Python Executable with PyInstaller" -ForegroundColor Cyan
pyinstaller --onefile --name Aperture.exe code_modification\main.py

Write-Host "Moving Binaries" -ForegroundColor Cyan
$destPath = "website\build\python\win"
if (!(Test-Path $destPath)) {
    New-Item -ItemType Directory -Force -Path $destPath
}

Copy-Item -Path "dist\Aperture.exe" -Destination "$destPath\aperture.exe" -Force
Write-Host "Building Electron App" -ForegroundColor Cyan
Set-Location website
npm install
npm install --save-dev electron-builder@^24.6.0
npx electron-builder --win --x64

Write-Host "Build completed" -ForegroundColor Green