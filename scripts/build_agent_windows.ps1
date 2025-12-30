Param(
  [string]$OutputDir = "dist",
  [string]$SpecArgs = "",
  [switch]$OneFile
)

# Build the fleet_agent.py into a single executable using PyInstaller.
# Usage: .\scripts\build_agent_windows.ps1 -OneFile

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  Write-Host "PyInstaller not found. Installing..."
  python -m pip install --upgrade pip
  python -m pip install pyinstaller
}

$scriptPath = Join-Path (Get-Location) 'fleet_agent.py'
if (-not (Test-Path $scriptPath)) { Write-Error "fleet_agent.py not found in repo root"; exit 1 }

$clean = "--clean"
$one = ""
if ($OneFile) { $one = "--onefile" }

Write-Host "Building agent..."
$cmd = "pyinstaller $clean $one --distpath $OutputDir $SpecArgs `"$scriptPath`""
Write-Host $cmd
Invoke-Expression $cmd

if (Test-Path "$OutputDir") { Write-Host "Build complete. Output: $OutputDir" } else { Write-Error "Build failed" }
