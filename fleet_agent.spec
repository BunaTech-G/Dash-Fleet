# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Fleet Agent with Windows system tray support

a = Analysis(
    ['fleet_agent.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('fleet_agent_windows_tray.py', '.'),
        ('fleet_utils.py', '.'),
        ('logging_config.py', '.'),
        ('constants.py', '.'),
    ],
    hiddenimports=[
        'pystray',
        'PIL',
        'psutil',
        'requests',
        'flask',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='fleet_agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
