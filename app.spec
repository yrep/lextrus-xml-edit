# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_data_files
import os
import sys

current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
venv_site_packages = os.path.join(current_dir, 'venv', 'Lib', 'site-packages')

def get_hidden_imports():
    return [
        'bs4',
        'lxml',
        'requests',
        'soupsieve',
        'certifi',
        'charset_normalizer',
        'idna',
        'urllib3',
        'typing_extensions',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'shiboken6'
    ]

def get_datas():
    return (
        collect_all('bs4')[0] +
        collect_all('lxml')[0] +
        collect_all('requests')[0] +
        collect_data_files('certifi') +
        [('./icons', 'icons')]
    )

a = Analysis(
    ['app.py'],
    pathex=[current_dir, venv_site_packages],
    binaries=[],
    datas=get_datas(),
    hiddenimports=get_hidden_imports(),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    upx=True,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
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
    icon='./app.ico',
    onefile=True
)