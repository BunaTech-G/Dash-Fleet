$ErrorActionPreference = 'Stop'
$packageName = 'dashfleet'
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Expect the agent exe shipped alongside the nuspec; copy to Program Files
$dest = Join-Path $env:ProgramFiles "DashFleet"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$exe = Join-Path $toolsDir 'files' 'fleet_agent.exe'
Copy-Item $exe -Destination $dest -Force

# Create scheduled task to run at startup
$taskName = 'DashFleetAgent'
$exePath = Join-Path $dest 'fleet_agent.exe'
$action = New-ScheduledTaskAction -Execute $exePath
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -RunLevel Highest -Force

Write-Host "DashFleet agent installed to $dest"
