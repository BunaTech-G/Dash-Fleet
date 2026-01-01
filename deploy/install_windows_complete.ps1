# ============================================================
# INSTALLATION AGENT DASHFLEET - WINDOWS
# ============================================================
# Exécuter en tant qu'Administrateur
# PowerShell 5.1+ requis

param(
    [string]$ServerUrl = "https://dash-fleet.com",
    [string]$ApiKey = "VOTRE_API_KEY_ICI",  # À récupérer depuis le dashboard
    [string]$MachineId = "",  # Laissez vide pour auto-générer
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Agent DashFleet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$InstallDir = "C:\Program Files\DashFleet"
$LogsDir = "$InstallDir\logs"
$ConfigFile = "$InstallDir\config.json"
$AgentFile = "$InstallDir\fleet_agent.py"
$UtilsFile = "$InstallDir\fleet_utils.py"
$VenvPath = "$InstallDir\.venv"

# Vérifier les droits admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'Administrateur!" -ForegroundColor Red
    exit 1
}

# Créer les répertoires
Write-Host "Création des répertoires..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

# Télécharger les fichiers depuis GitHub
Write-Host "Téléchargement de fleet_agent.py..." -ForegroundColor Yellow
$AgentUrl = "https://raw.githubusercontent.com/BunaTech-G/Dashboard-syst-me-/fix/pyproject-exclude/fleet_agent.py"
Invoke-WebRequest -Uri $AgentUrl -OutFile $AgentFile

Write-Host "Téléchargement de fleet_utils.py..." -ForegroundColor Yellow
$UtilsUrl = "https://raw.githubusercontent.com/BunaTech-G/Dashboard-syst-me-/fix/pyproject-exclude/fleet_utils.py"
Invoke-WebRequest -Uri $UtilsUrl -OutFile $UtilsFile

# Créer l'environnement virtuel
Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
python -m venv $VenvPath

# Installer les dépendances
Write-Host "Installation des dépendances..." -ForegroundColor Yellow
& "$VenvPath\Scripts\pip.exe" install --upgrade pip --quiet
& "$VenvPath\Scripts\pip.exe" install psutil requests --quiet

# Générer machine_id si nécessaire
if ([string]::IsNullOrEmpty($MachineId)) {
    $MachineId = $env:COMPUTERNAME.ToLower()
    Write-Host "Machine ID auto-généré: $MachineId" -ForegroundColor Green
}

# Créer le fichier de configuration
Write-Host "Création du fichier de configuration..." -ForegroundColor Yellow
$Config = @{
    server = $ServerUrl
    path = "/api/fleet/report"
    token = $ApiKey
    interval = $IntervalSeconds
    machine_id = $MachineId
    log_file = "$LogsDir\agent.log"
} | ConvertTo-Json

$Config | Out-File -FilePath $ConfigFile -Encoding UTF8

# Créer une tâche planifiée
Write-Host "Création de la tâche planifiée..." -ForegroundColor Yellow
$TaskName = "DashFleet Agent"
$Action = New-ScheduledTaskAction -Execute "$VenvPath\Scripts\python.exe" -Argument "`"$AgentFile`"" -WorkingDirectory $InstallDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings | Out-Null

# Démarrer l'agent immédiatement
Write-Host "Démarrage de l'agent..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName

Write-Host "" 
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation terminée avec succès!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:"
Write-Host "  - Répertoire: $InstallDir"
Write-Host "  - Machine ID: $MachineId"
Write-Host "  - Serveur: $ServerUrl"
Write-Host "  - Intervalle: $IntervalSeconds secondes"
Write-Host ""
Write-Host "Vérifier les logs: $LogsDir\agent.log"
Write-Host "Tâche planifiée: $TaskName"
Write-Host ""
Write-Host "Pour vérifier le statut:"
Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
