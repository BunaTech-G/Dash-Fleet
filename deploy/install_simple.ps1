# PowerShell installer snippet for DashFleet on Windows (simplified)
# Run as Administrator
# Usage: powershell -ExecutionPolicy Bypass -File install_simple.ps1 -ApiKey "your_key"

param(
    [string]$ApiKey = "d2f6f9a8-3c7e-4c1f-9b0f-123456789abc",
    [string]$ServerUrl = "https://dash-fleet.com",
    [string]$MachineId = $env:COMPUTERNAME.ToLower()
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Agent DashFleet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Vérifier les droits admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'Administrateur!" -ForegroundColor Red
    exit 1
}

# Vérifier que Python est installé
Write-Host "Vérification de Python..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "ERREUR: Python n'est pas installé ou n'est pas dans le PATH!" -ForegroundColor Red
    Write-Host "Installez Python depuis https://www.python.org/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Python trouvé: $pythonPath" -ForegroundColor Green

# Configuration
$InstallDir = "C:\DashFleet"
$LogsDir = "$InstallDir\logs"
$ConfigFile = "$InstallDir\config.json"
$AgentFile = "$InstallDir\fleet_agent.py"
$UtilsFile = "$InstallDir\fleet_utils.py"

# Créer les répertoires
Write-Host "Création des répertoires..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

# Télécharger les fichiers depuis GitHub
Write-Host "Téléchargement de fleet_agent.py..." -ForegroundColor Yellow
$AgentUrl = "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/fleet_agent.py"
try {
    Invoke-WebRequest -Uri $AgentUrl -OutFile $AgentFile -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ fleet_agent.py téléchargé" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de télécharger fleet_agent.py" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "Téléchargement de fleet_utils.py..." -ForegroundColor Yellow
$UtilsUrl = "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/fleet_utils.py"
try {
    Invoke-WebRequest -Uri $UtilsUrl -OutFile $UtilsFile -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ fleet_utils.py téléchargé" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de télécharger fleet_utils.py" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Installer les dépendances
Write-Host "Installation des dépendances Python..." -ForegroundColor Yellow
try {
    & python -m pip install --upgrade pip --quiet
    & python -m pip install psutil requests --quiet
    Write-Host "✅ Dépendances installées" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible d'installer les dépendances" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Créer le fichier de configuration
Write-Host "Création du fichier de configuration..." -ForegroundColor Yellow
$Config = @{
    server = $ServerUrl
    path = "/api/fleet/report"
    token = $ApiKey
    interval = 30
    machine_id = $MachineId
    log_file = "$LogsDir\agent.log"
} | ConvertTo-Json

$Config | Out-File -FilePath $ConfigFile -Encoding UTF8
Write-Host "✅ Configuration créée" -ForegroundColor Green

# Créer une tâche planifiée
Write-Host "Création de la tâche planifiée..." -ForegroundColor Yellow
$TaskName = "DashFleet Agent"

# Vérifier si la tâche existe et la supprimer
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
}

# Créer la nouvelle tâche
$Action = New-ScheduledTaskAction -Execute "$pythonPath" -Argument "`"$AgentFile`"" -WorkingDirectory $InstallDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
    Write-Host "✅ Tâche planifiée créée" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de créer la tâche planifiée" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Démarrer l'agent immédiatement
Write-Host "Démarrage de l'agent..." -ForegroundColor Yellow
try {
    Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Start-Sleep -Seconds 2
    Write-Host "✅ Agent démarré" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Impossible de démarrer l'agent" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation terminée avec succès!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  - Répertoire: $InstallDir" -ForegroundColor Gray
Write-Host "  - Machine ID: $MachineId" -ForegroundColor Gray
Write-Host "  - Serveur: $ServerUrl" -ForegroundColor Gray
Write-Host "  - API Key: $($ApiKey.Substring(0, 8))..." -ForegroundColor Gray
Write-Host ""
Write-Host "Voir les logs:" -ForegroundColor White
Write-Host "  Get-Content '$LogsDir\agent.log' -Tail 20" -ForegroundColor Green
Write-Host ""
Write-Host "Vérifier le statut:" -ForegroundColor White
Write-Host "  Get-ScheduledTask -TaskName 'DashFleet Agent' | Get-ScheduledTaskInfo" -ForegroundColor Green
Write-Host ""
Write-Host "L'agent tourne maintenant et envoie les métriques toutes les 30 secondes!" -ForegroundColor Cyan
