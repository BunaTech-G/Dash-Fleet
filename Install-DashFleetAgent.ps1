# DashFleet Agent - Professional Windows Installer
# This script installs and configures DashFleet Agent with system tray support

param(
    [string]$ServerUrl = "https://dash-fleet.com",
    [string]$MachineId = $env:COMPUTERNAME,
    [switch]$NoTray = $false,
    [switch]$Uninstall = $false
)

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

# Colors for output
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Header { Write-Host "`n=== $args ===" -ForegroundColor Magenta }

Write-Header "DashFleet Agent Professional Installer"

# Check if running as admin
function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Error "This script must be run as Administrator!"
    Write-Info "Please right-click PowerShell and select 'Run as administrator'"
    exit 1
}

# ============================================================================
# UNINSTALL
# ============================================================================

if ($Uninstall) {
    Write-Header "Uninstalling DashFleet Agent"
    
    # Remove from startup
    $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    if (Get-ItemProperty -Path $regPath -Name "DashFleetAgent" -ErrorAction SilentlyContinue) {
        Remove-ItemProperty -Path $regPath -Name "DashFleetAgent"
        Write-Success "Removed from auto-start"
    }
    
    # Stop any running agent
    $process = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*fleet_agent*" }
    if ($process) {
        Stop-Process -InputObject $process -Force
        Write-Success "Stopped running agent"
    }
    
    # Remove installation folder
    $installPath = "C:\Program Files\DashFleet"
    if (Test-Path $installPath) {
        Remove-Item -Path $installPath -Recurse -Force
        Write-Success "Removed installation folder"
    }
    
    Write-Success "DashFleet Agent uninstalled successfully"
    exit 0
}

# ============================================================================
# INSTALL PYTHON IF NEEDED
# ============================================================================

Write-Header "Checking Python Installation"

$pythonPath = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Info "Python not found in PATH"
    Write-Info "Attempting to find Python installation..."
    
    $pythonPaths = @(
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python310\python.exe"
    )
    
    foreach ($path in $pythonPaths) {
        if (Test-Path $path) {
            $pythonPath = $path
            break
        }
    }
    
    if (-not $pythonPath) {
        Write-Error "Python 3.10+ is required but not installed"
        Write-Info "Please download Python from https://www.python.org/"
        Write-Info "Make sure to check 'Add Python to PATH' during installation"
        exit 1
    }
}

Write-Success "Found Python: $pythonPath"

# Verify Python version
$pythonVersion = & $pythonPath --version 2>&1
Write-Success "Python version: $pythonVersion"

# ============================================================================
# CREATE INSTALLATION FOLDER
# ============================================================================

Write-Header "Creating Installation Directory"

$installPath = "C:\Program Files\DashFleet"
$agentScript = Join-Path $installPath "agent.py"

if (-not (Test-Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    Write-Success "Created: $installPath"
}

# ============================================================================
# DOWNLOAD AGENT
# ============================================================================

Write-Header "Downloading DashFleet Agent"

$repoUrl = "https://github.com/BunaTech-G/Dash-Fleet/raw/feat/react-spa/fleet_agent_pro.py"
Write-Info "Downloading from: $repoUrl"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $repoUrl -OutFile $agentScript -UseBasicParsing -ErrorAction Stop
    Write-Success "Downloaded agent to: $agentScript"
} catch {
    Write-Error "Failed to download agent: $_"
    exit 1
}

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================

Write-Header "Installing Python Dependencies"

$dependencies = @("psutil", "pillow", "pystray")

foreach ($package in $dependencies) {
    Write-Info "Installing $package..."
    try {
        & $pythonPath -m pip install $package --quiet 2>$null
        Write-Success "Installed: $package"
    } catch {
        Write-Error "Failed to install $package"
    }
}

# ============================================================================
# CREATE LAUNCHER SCRIPTS
# ============================================================================

Write-Header "Creating Launcher Scripts"

# Create batch launcher (for visible console window)
$batchLauncher = Join-Path $installPath "start-agent.bat"
@"
@echo off
REM DashFleet Agent Launcher
python "%~dp0agent.py" --server "$ServerUrl" --machine-id "$MachineId"
pause
"@ | Set-Content -Path $batchLauncher -Encoding ASCII
Write-Success "Created: $batchLauncher"

# Create VBS launcher (for silent startup)
$vbsLauncher = Join-Path $installPath "start-agent-silent.vbs"
@"
' DashFleet Agent Silent Launcher
Set objFSO = CreateObject("Scripting.FileSystemObject")
pythonPath = "$pythonPath"
agentPath = "$agentScript"
serverUrl = "$ServerUrl"
machineId = "$MachineId"

Set objShell = CreateObject("WScript.Shell")
cmd = pythonPath & " """ & agentPath & """ --server " & serverUrl & " --machine-id " & machineId
objShell.Run cmd, 0, False
"@ | Set-Content -Path $vbsLauncher -Encoding ASCII
Write-Success "Created: $vbsLauncher"

# ============================================================================
# CREATE START MENU SHORTCUTS
# ============================================================================

Write-Header "Creating Start Menu Shortcuts"

$startMenu = [Environment]::GetFolderPath("Programs")
$dashfleetFolder = Join-Path $startMenu "DashFleet"

if (-not (Test-Path $dashfleetFolder)) {
    New-Item -ItemType Directory -Path $dashfleetFolder -Force | Out-Null
}

# Shortcut for visible window
$shortcutPath = Join-Path $dashfleetFolder "DashFleet Agent.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batchLauncher
$shortcut.WorkingDirectory = $installPath
$shortcut.Description = "Run DashFleet Agent"
$shortcut.IconLocation = "C:\Windows\System32\shell32.dll,1"
$shortcut.Save()
Write-Success "Created shortcut: $shortcutPath"

# Shortcut for settings
$settingsPath = Join-Path $dashfleetFolder "Settings.lnk"
$shortcut2 = $shell.CreateShortcut($settingsPath)
$shortcut2.TargetPath = $installPath
$shortcut2.WorkingDirectory = $installPath
$shortcut2.Description = "DashFleet Agent Installation Directory"
$shortcut2.Save()
Write-Success "Created settings link: $settingsPath"

# ============================================================================
# CONFIGURE AUTO-START
# ============================================================================

Write-Header "Configuring Auto-Start"

$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$cmdLine = "`"$pythonPath`" `"$agentScript`" --server $ServerUrl --machine-id $MachineId"

New-Item -Path $regPath -Force | Out-Null
New-ItemProperty -Path $regPath -Name "DashFleetAgent" -Value $cmdLine -PropertyType String -Force | Out-Null
Write-Success "Agent will auto-start on next Windows boot"

# ============================================================================
# FIRST RUN TEST
# ============================================================================

Write-Header "Testing Agent Installation"

Write-Info "Running agent test (will run for 5 seconds)..."
$testTimeout = 5
$testProcess = Start-Process -FilePath $pythonPath -ArgumentList @($agentScript, "--server", $ServerUrl, "--machine-id", $MachineId) -PassThru -NoNewWindow

Start-Sleep -Seconds $testTimeout
if ($testProcess.HasExited -eq $false) {
    Stop-Process -InputObject $testProcess -Force -ErrorAction SilentlyContinue
}

Write-Success "Agent test completed"

# ============================================================================
# SUMMARY
# ============================================================================

Write-Header "Installation Complete!"

Write-Host @"

DashFleet Agent has been installed successfully!

📊 Configuration:
   - Server URL: $ServerUrl
   - Machine ID: $MachineId
   - Installation: $installPath
   - Auto-start: Enabled

🚀 How to Start:
   1. From Start Menu: Search for "DashFleet Agent"
   2. Or run manually: $batchLauncher
   3. Or run silently (on boot): Via registry

📝 Log Location:
   $env:USERPROFILE\dashfleet_agent.log

🛠️ To Uninstall:
   powershell -ExecutionPolicy Bypass -Command "& '$($MyInvocation.MyCommand.Path)' -Uninstall"

❓ Help:
   Run: python "$agentScript" --help

"@

Write-Success "Setup Complete! The agent will start automatically on next boot."
Write-Info "You can also manually start it from the Start Menu."

# Create a helpful README
$readmePath = Join-Path $installPath "README.txt"
@"
DashFleet Agent Installation

WHAT'S INCLUDED:
- fleet_agent_pro.py: Main agent application
- start-agent.bat: Launch with visible window
- start-agent-silent.vbs: Launch silently (used for auto-start)

CONFIGURATION:
Server URL: $ServerUrl
Machine ID: $MachineId

AUTO-START:
The agent will automatically start when Windows boots.
You can disable this in Windows Settings > Apps > Startup.

LOGS:
Check logs at: $env:USERPROFILE\dashfleet_agent.log

HELP:
Run: python agent.py --help
"@ | Set-Content -Path $readmePath -Encoding UTF8

Write-Success "Created README: $readmePath"

Read-Host "Press Enter to close this window"
