#Requires -RunAsAdministrator
<#
.SYNOPSIS
Configure DashFleet Agent as a Windows Scheduled Task with auto-start

.PARAMETER ApiKey
The API key for authentication (required)

.PARAMETER MachineId
Custom machine identifier (defaults to computer name)

.PARAMETER Server
Server URL (defaults to https://dash-fleet.com)

.PARAMETER Interval
Reporting interval in seconds (defaults to 30)

.PARAMETER AgentPath
Path to dashfleet-agent.exe (defaults to C:\Program Files\DashFleet\dashfleet-agent.exe)

.PARAMETER LogPath
Path to agent log file (defaults to C:\Program Files\DashFleet\logs\agent.log)

.EXAMPLE
.\setup_scheduled_task.ps1 -ApiKey "api_a7ee4957ca1640e180802c256fdf" -MachineId "OSIDIBE-PC"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey,
    
    [Parameter(Mandatory=$false)]
    [string]$MachineId = $env:COMPUTERNAME,
    
    [Parameter(Mandatory=$false)]
    [string]$Server = "https://dash-fleet.com",
    
    [Parameter(Mandatory=$false)]
    [int]$Interval = 30,
    
    [Parameter(Mandatory=$false)]
    [string]$AgentPath = "C:\Program Files\DashFleet\dashfleet-agent.exe",
    
    [Parameter(Mandatory=$false)]
    [string]$LogPath = "C:\Program Files\DashFleet\logs\agent.log"
)

# Verify we're running as administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DashFleet Agent - Scheduled Task Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if agent exists
if (-not (Test-Path $AgentPath)) {
    Write-Host "ERROR: Agent executable not found at: $AgentPath" -ForegroundColor Red
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Machine ID: $MachineId"
Write-Host "  Server: $Server"
Write-Host "  API Key: $($ApiKey.Substring(0,10))..."
Write-Host "  Interval: ${Interval}s"
Write-Host "  Agent Path: $AgentPath"
Write-Host "  Log Path: $LogPath"
Write-Host ""

# Ensure logs directory exists
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path $LogDir)) {
    Write-Host "Creating logs directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Build command arguments
$Arguments = @(
    "--server", $Server,
    "--token", $ApiKey,
    "--machine-id", $MachineId,
    "--interval", $Interval.ToString(),
    "--log-file", $LogPath
)

Write-Host "Setting up scheduled task..." -ForegroundColor Yellow

# Remove existing task if it exists
$TaskName = "DashFleet Agent"
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
}

# Create trigger (at startup)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $AgentPath `
    -Argument ($Arguments -join " ")

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Register the task with highest privileges
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -RunLevel Highest `
        -ErrorAction Stop | Out-Null
    
    Write-Host "✓ Scheduled task created successfully" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

# Start the task
Write-Host "Starting agent..." -ForegroundColor Yellow
try {
    Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Start-Sleep -Seconds 2
    Write-Host "✓ Agent started" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to start task: $_" -ForegroundColor Red
    exit 1
}

# Get task info
$TaskInfo = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Task Status:" -ForegroundColor Green
Write-Host "  Task Name: $($TaskName)"
Write-Host "  State: $($(Get-ScheduledTask -TaskName $TaskName).State)"
Write-Host "  Next Run: $($TaskInfo.NextRunTime)"
Write-Host ""

Write-Host "Verification Commands:" -ForegroundColor Green
Write-Host "  Check status: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  View logs: Get-Content '$LogPath' -Tail 20"
Write-Host "  Restart task: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""

Write-Host "The agent will:" -ForegroundColor Green
Write-Host "  • Start automatically on system boot"
Write-Host "  • Run with highest privileges"
Write-Host "  • Send metrics every ${Interval} seconds"
Write-Host "  • Log to: $LogPath"
Write-Host ""

Write-Host "Dashboard: $Server/fleet" -ForegroundColor Cyan
Write-Host ""
