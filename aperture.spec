# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('code_modification', 'code_modification'),
    ('aperture_library', 'aperture_library'),
]
binaries = []
hiddenimports = [
    'github', 'github.Auth', 'github.GithubException',
    'git', 'gitdb', 'gitdb.db', 'smmap',
    'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna',
    'pyperclip', 'huggingface_hub', 'edge_tts',
    'vosk', 'pyaudio', 'keyboard', 'pyautogui', 'pyglet', 'pygame',
]

collect_packages = [
    'github', 'git', 'gitdb', 'smmap',
    'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna',
    'pyperclip', 'huggingface_hub', 'edge_tts',
    'vosk', 'pyaudio', 'keyboard', 'pyautogui', 'pyglet', 'pygame',
]
for pkg in collect_packages:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    except Exception:
        pass


a = Analysis(
    ['code_modification/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Aperture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
