param(
    [string]$ServerUrl = "https://mon-serveur-mdm.example.com",
    [string]$FleetToken = "REMPLACER_PAR_FLEET_TOKEN",
    [int]$IntervalSeconds = 30,
    [string]$InstallDir = "C:\ProgramData\mini-mdm-agent",
    [string]$ServiceName = "MiniMDMAgent",
    [string]$PythonExe = ""
)

# Vérifie les privilèges admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Exécutez ce script dans un PowerShell en mode Administrateur."; exit 1
}

$ErrorActionPreference = "Stop"

# Prépare les chemins
$installPath = $InstallDir.TrimEnd('\')
$logsPath = Join-Path $installPath "logs"
$configPath = Join-Path $installPath "config.json"
$agentPath = Join-Path $installPath "fleet_agent.py"
$venvPath = Join-Path $installPath "venv"
if ([string]::IsNullOrWhiteSpace($PythonExe)) { $PythonExe = Join-Path $venvPath "Scripts\python.exe" }

# Création dossiers
New-Item -ItemType Directory -Force -Path $installPath | Out-Null
New-Item -ItemType Directory -Force -Path $logsPath | Out-Null

# Copie de l'agent
Copy-Item -Path "$PSScriptRoot\..\fleet_agent.py" -Destination $agentPath -Force

# Venv + dépendances
python -m venv $venvPath
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install psutil requests

# Config JSON
$config = [ordered]@{
    server    = $ServerUrl
    path      = "/api/fleet/report"
    token     = $FleetToken
    interval  = $IntervalSeconds
    machine_id= ""
    log_file  = (Join-Path $logsPath "agent.log")
}
$config | ConvertTo-Json -Depth 3 | Set-Content -Path $configPath -Encoding UTF8

# Service Windows
$bin = '"{0}" "{1}" --config "{2}"' -f $PythonExe, $agentPath, $configPath
try { sc.exe stop $ServiceName | Out-Null } catch {}
try { sc.exe delete $ServiceName | Out-Null } catch {}
sc.exe create $ServiceName binPath= $bin start= auto DisplayName= "Mini MDM Agent"
sc.exe failure $ServiceName reset= 60 actions= restart/5000/restart/5000/restart/5000

# Démarrage
sc.exe start $ServiceName
Write-Host "Service $ServiceName installé et démarré."