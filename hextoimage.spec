# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the project root directory (where this spec file is located)
project_root = Path('D:/PROYECTOS EN CURSO/Python/hextoimage')

# Add the src directory to Python path
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

block_cipher = None

a = Analysis(
    ['gui_launcher.py'],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=[
        # Include the assets directory
        (str(project_root / 'assets'), 'assets'),
        # Include all Python files from src directory
        (str(src_path), 'src'),
    ],
    hiddenimports=[
        'src.gui.main_window',
        'src.gui.__init__',
        'src.gui',
        'src.core.hex_reader',
        'src.core.analyzers', 
        'src.core.exporters',
        'src.core.formatters',
        'src.core.signatures',
        'src.core.validators',
        'src.core.__init__',
        'src.core',
        'src.__init__',
        'src',
        'gui.main_window',
        'gui',
        'core.hex_reader',
        'core.analyzers',
        'core.exporters',
        'core.formatters',
        'core.signatures',
        'core.validators',
        'core',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'threading',
        'pathlib',
        'tempfile',
        'io',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HexToImage',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.png'),
)
