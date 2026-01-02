# Install DashFleet agent from bundled EXE (no external Python needed)
# Usage (PowerShell as Admin):
#   .\install_agent_exe.ps1 -ApiKey "YOUR_TOKEN" -MachineId "host-01"
param(
    [Parameter(Mandatory=$true)][string]$ApiKey,
    [string]$MachineId = $env:COMPUTERNAME,
    [string]$ServerUrl = "https://dash-fleet.com",
    [string]$Interval = "30"
)

$ErrorActionPreference = "Stop"

# Admin check
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERREUR: lancer en Administrateur" -ForegroundColor Red
    exit 1
}

# Locate EXE
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = Join-Path $ScriptDir "bin\dashfleet-agent.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "ERREUR: $ExePath introuvable. Construisez-le avec deploy/build_agent_exe.ps1" -ForegroundColor Red
    exit 1
}

# Install paths
$BaseDir = "C:\\Program Files\\DashFleet"
if (-not (Test-Path $BaseDir)) {
    $BaseDir = "C:\\DashFleet"
}
$AgentDir = $BaseDir
$LogsDir = Join-Path $AgentDir "logs"
$ConfigPath = Join-Path $AgentDir "config.json"

New-Item -ItemType Directory -Path $AgentDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

# Copy EXE
Copy-Item $ExePath -Destination (Join-Path $AgentDir "dashfleet-agent.exe") -Force

# Write config (UTF-8 sans BOM)
$config = @"
{
    "server": "$ServerUrl",
    "path": "/api/fleet/report",
    "token": "$ApiKey",
    "interval": $Interval,
    "machine_id": "$MachineId",
    "log_file": "$LogsDir\\agent.log"
}
"@
[System.IO.File]::WriteAllText($ConfigPath, $config, (New-Object System.Text.UTF8Encoding $false))

# Create scheduled task
$TaskName = "DashFleet Agent"
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null }

$Action = New-ScheduledTaskAction -Execute (Join-Path $AgentDir "dashfleet-agent.exe") -Argument "--config `"$ConfigPath`"" -WorkingDirectory $AgentDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null

# Start now
Start-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Installation OK" -ForegroundColor Green
Write-Host "EXE: $AgentDir\dashfleet-agent.exe"
Write-Host "Config: $ConfigPath"
Write-Host "Logs: $LogsDir\agent.log"
Write-Host "Tâche planifiée: $TaskName"
Write-Host "Dashboard: https://dash-fleet.com/fleet"
