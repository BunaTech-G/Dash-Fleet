# Build DashFleet agent into a standalone EXE (PyInstaller)
# Uses: deploy/specs/agent.spec
# Usage (PowerShell):
#   cd deploy
#   .\build_agent_exe.ps1
# Output: dist\dashfleet-agent\dashfleet-agent.exe
param(
    [string]$PythonVersion = "3.11.7"
)

$ErrorActionPreference = "Stop"

# Paths
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BuildRoot = Join-Path $PSScriptRoot ".build"
$VenvDir = Join-Path $BuildRoot "venv"
$OutputDir = Join-Path $RepoRoot "dist"
$SpecFile = Join-Path $PSScriptRoot "specs\agent.spec"

# Clean build folders
if (Test-Path $BuildRoot) { Remove-Item $BuildRoot -Recurse -Force }
New-Item -ItemType Directory -Path $BuildRoot | Out-Null

Write-Host "[1/2] Creating venv..." -ForegroundColor Cyan
python -m venv $VenvDir

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host "[2/2] Installing dependencies (psutil, requests, pyinstaller)..." -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip > $null
& $VenvPython -m pip install psutil requests pyinstaller > $null

Write-Host "[3/2] Building with PyInstaller..." -ForegroundColor Cyan
& $VenvPython -m PyInstaller --distpath $OutputDir --workpath $BuildRoot\build --specpath $BuildRoot $SpecFile

Write-Host "[✓] Build complete!" -ForegroundColor Green
Write-Host "EXE: $OutputDir\dashfleet-agent\dashfleet-agent.exe" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "Verify:" -ForegroundColor Cyan
Write-Host "  .\dist\dashfleet-agent\dashfleet-agent.exe --help" -ForegroundColor Gray
             excludes=[])
pyo = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyo,
          a.scripts,
          [],
          exclude_binaries=True,
          name='$ExeName',
          debug=False,

