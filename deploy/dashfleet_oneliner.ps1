# DashFleet Agent - One-Liner Setup for New Machines
# Usage: 
#   1. Télécharger l'executable depuis: https://github.com/BunaTech-G/Dash-Fleet/releases
#   2. Exécuter dans PowerShell (en tant qu'administrateur):
#
# Powershell -NoProfile -ExecutionPolicy Bypass -Command "IEX ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/dashfleet_oneliner.ps1')) -ApiKey 'api_xxx' -MachineId 'MACHINE-NAME'"

# AVEC CE SCRIPT:
# powershell -NoProfile -ExecutionPolicy Bypass -File C:\deploy\setup_scheduled_task.ps1 -ApiKey 'api_xxx' -MachineId 'MACHINE-NAME'

# OU INTERACTIVEMENT:
# C:\Program Files\DashFleet\dashfleet-agent.exe --server https://dash-fleet.com --token api_xxx --machine-id MACHINE-NAME

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DashFleet Agent - Installation Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if running as admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "`nERROR: Please run this script as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Download and run setup script
$ScriptPath = "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/setup_scheduled_task.ps1"
Write-Host "`nDownloading setup script..." -ForegroundColor Yellow

try {
    $SetupScript = (New-Object System.Net.WebClient).DownloadString($ScriptPath)
    Write-Host "Script downloaded successfully" -ForegroundColor Green
    
    # Execute with parameters
    # The parameters should be passed via the command that calls this script
    Write-Host "Run this to setup the agent:" -ForegroundColor Cyan
    Write-Host "  powershell -File setup_scheduled_task.ps1 -ApiKey 'YOUR_API_KEY' -MachineId 'YOUR_MACHINE_NAME'" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to download setup script: $_" -ForegroundColor Red
    exit 1
}
