# One-liner DashFleet Agent installer (Windows)
# Usage (PowerShell as Admin):
#   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_oneliner.ps1" -OutFile "$env:TEMP\install.ps1"; & "$env:TEMP\install.ps1" -ApiKey "YOUR_TOKEN"

param(
    [Parameter(Mandatory=$true)][string]$ApiKey,
    [string]$MachineId = $env:COMPUTERNAME,
    [string]$ServerUrl = "https://dash-fleet.com",
    [string]$Interval = "30"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DashFleet Agent Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Admin check
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERREUR: Ce script doit etre lance en Administrateur" -ForegroundColor Red
    Write-Host "Relancez PowerShell en tant qu'Administrateur et reessayez." -ForegroundColor Yellow
    exit 1
}

# Install paths
$BaseDir = "C:\Program Files\DashFleet"
if (-not (Test-Path $BaseDir)) {
    $BaseDir = "C:\DashFleet"
}
$AgentDir = $BaseDir
$LogsDir = Join-Path $AgentDir "logs"
$ConfigPath = Join-Path $AgentDir "config.json"
$ExePath = Join-Path $AgentDir "dashfleet-agent.exe"

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Machine: $MachineId" -ForegroundColor Gray
Write-Host "  Serveur: $ServerUrl" -ForegroundColor Gray
Write-Host "  Repertoire: $AgentDir" -ForegroundColor Gray
Write-Host ""

# Create directories
Write-Host "Preparation des repertoires..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $AgentDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

# Download EXE from GitHub
Write-Host "Telechargement de l'agent depuis GitHub..." -ForegroundColor Yellow
$GithubUrl = "https://github.com/BunaTech-G/Dash-Fleet/raw/fix/pyproject-exclude/deploy/bin/dashfleet-agent.exe"
$TempExe = Join-Path $env:TEMP "dashfleet-agent-temp.exe"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $GithubUrl -OutFile $TempExe -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ Agent telecharge" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de telecharger l'agent" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Copy EXE
try {
    Copy-Item $TempExe -Destination $ExePath -Force
    Remove-Item $TempExe -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Agent copie dans $AgentDir" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de copier l'agent" -ForegroundColor Red
    exit 1
}

# Write config (UTF-8 sans BOM)
Write-Host "Creation de la configuration..." -ForegroundColor Yellow
$config = @"
{
    "server": "$ServerUrl",
    "path": "/api/fleet/report",
    "token": "$ApiKey",
    "interval": $Interval,
    "machine_id": "$MachineId",
    "log_file": "$LogsDir\agent.log"
}
"@

try {
    [System.IO.File]::WriteAllText($ConfigPath, $config, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "✅ Configuration creee" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de creer la configuration" -ForegroundColor Red
    exit 1
}

# Create scheduled task
Write-Host "Creation de la tache planifiee..." -ForegroundColor Yellow
$TaskName = "DashFleet Agent"

# Remove existing task
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    } catch {}
}

try {
    $Action = New-ScheduledTaskAction -Execute $ExePath -Argument "--config `"$ConfigPath`"" -WorkingDirectory $AgentDir
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
    Write-Host "✅ Tache planifiee creee" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de creer la tache planifiee" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Start agent immediately
Write-Host "Demarrage de l'agent..." -ForegroundColor Yellow
try {
    Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Start-Sleep -Seconds 2
    Write-Host "✅ Agent demarrE" -ForegroundColor Green
} catch {
    Write-Host "ATTENTION: La tache ne s'est pas demarree immediatement" -ForegroundColor Yellow
    Write-Host "Elle demarrera au prochain redemarrage du PC." -ForegroundColor Yellow
}

# Verify
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation reussie !" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Agent EXE: $ExePath" -ForegroundColor Gray
Write-Host "  Config: $ConfigPath" -ForegroundColor Gray
Write-Host "  Logs: $LogsDir\agent.log" -ForegroundColor Gray
Write-Host "  Tache: $TaskName" -ForegroundColor Gray
Write-Host ""
Write-Host "Verification:" -ForegroundColor White
Write-Host "  Statut tache: Get-ScheduledTask -TaskName 'DashFleet Agent'" -ForegroundColor Green
Write-Host "  Derniers logs: Get-Content '$LogsDir\agent.log' -Tail 10" -ForegroundColor Green
Write-Host "  Machines: Invoke-RestMethod -Uri '$ServerUrl/api/fleet/public' -Method Get | ConvertTo-Json" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard: $ServerUrl/fleet" -ForegroundColor Cyan
Write-Host ""
Write-Host "L'agent se lancera automatiquement au demarrage du PC et envoie les metriques toutes les $Interval secondes." -ForegroundColor Cyan
