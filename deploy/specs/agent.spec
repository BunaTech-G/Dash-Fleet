# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for DashFleet Agent (fleet_agent.py)
# Build: pyinstaller deploy/specs/agent.spec

import os

# Use relative paths for portability
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fleet_agent = os.path.join(repo_root, 'fleet_agent.py')
fleet_utils = os.path.join(repo_root, 'fleet_utils.py')

a = Analysis(
    [fleet_agent],
    pathex=[repo_root],
    binaries=[],
    datas=[(fleet_utils, '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='dashfleet-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=['icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='dashfleet-agent',
)
