# Build DashFleet agent into a standalone EXE (PyInstaller)
# Usage (PowerShell):
#   cd deploy
#   .\build_agent_exe.ps1 -PythonVersion 3.11.7
# Output: deploy\bin\dashfleet-agent.exe
param(
    [string]$PythonVersion = "3.11.7"
)

$ErrorActionPreference = "Stop"

# Paths
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BuildRoot = Join-Path $PSScriptRoot ".build"
$VenvDir = Join-Path $BuildRoot "venv"
$OutputDir = Join-Path $PSScriptRoot "bin"
$ExeName = "dashfleet-agent.exe"

# Clean build folders
if (Test-Path $BuildRoot) { Remove-Item $BuildRoot -Recurse -Force }
New-Item -ItemType Directory -Path $BuildRoot | Out-Null
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "[1/4] Creating venv..." -ForegroundColor Cyan
python -m venv $VenvDir

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host "[2/4] Installing dependencies (psutil, requests, pyinstaller)..." -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip > $null
& $VenvPython -m pip install psutil requests pyinstaller > $null

# PyInstaller spec
$SpecPath = Join-Path $BuildRoot "agent.spec"
$MainPath = Join-Path $RepoRoot "fleet_agent.py"
$UtilsPath = Join-Path $RepoRoot "fleet_utils.py"

$spec = @"
a = Analysis(['$MainPath'],
             pathex=['$RepoRoot'],
             binaries=[],
             datas=[('$UtilsPath','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[])
pyo = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyo,
          a.scripts,
          [],
          exclude_binaries=True,
          name='$ExeName',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='$ExeName')
"@
$spec | Out-File -FilePath $SpecPath -Encoding ASCII

Write-Host "[3/4] Building EXE (PyInstaller)..." -ForegroundColor Cyan
Push-Location $BuildRoot
& $VenvPython -m PyInstaller $SpecPath --onefile --noconfirm --distpath $OutputDir --workpath $BuildRoot\build > $null
Pop-Location

Write-Host "[4/4] Build finished." -ForegroundColor Green
Write-Host "EXE: $OutputDir\$ExeName"
