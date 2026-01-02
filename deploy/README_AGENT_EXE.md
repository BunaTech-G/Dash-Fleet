# DashFleet Agent EXE (Windows)

Installateur autonome sans dépendance Python.

## Contenu
- build_agent_exe.ps1 : construit l'EXE autonome (PyInstaller).
- install_agent_exe.ps1 : installe l'EXE sur un poste (copie, config, tâche planifiée).
- bin/dashfleet-agent.exe : produit par le build (non versionné par défaut).

## Prérequis
- Windows (PowerShell en Administrateur pour l'installation).
- Accès Internet pour télécharger les sources lors du build.

## Construction de l'EXE (à faire une fois)
```powershell
cd deploy
./build_agent_exe.ps1
```
Résultat : deploy/bin/dashfleet-agent.exe

## Installation sur un poste client (sans Python)
```powershell
cd deploy
./install_agent_exe.ps1 -ApiKey "VOTRE_API_KEY" -MachineId "$env:COMPUTERNAME"
```
Ce que fait le script :
- Copie l'EXE vers C:\Program Files\DashFleet\ (fallback C:\DashFleet\)
- Génère config.json (UTF-8 sans BOM) avec le token et le hostname réel
- Crée logs/agent.log
- Enregistre la tâche planifiée "DashFleet Agent" (SYSTEM, démarrage)
- Lance l'agent immédiatement

## Vérifications
```powershell
Get-ScheduledTask -TaskName "DashFleet Agent"
Get-Content "C:\DashFleet\logs\agent.log" -Tail 10
Invoke-RestMethod -Uri "https://dash-fleet.com/api/fleet/public" -Method Get | ConvertTo-Json
```

## Mise à jour / Réinstallation
Relancer install_agent_exe.ps1 (il remplace l'EXE, régénère la config et la tâche).

## Désinstallation
```powershell
Unregister-ScheduledTask -TaskName "DashFleet Agent" -Confirm:$false
Remove-Item "C:\DashFleet" -Recurse -Force  # ou "C:\Program Files\DashFleet"
```

## Linux (rappel)
Installer l'agent avec :
```bash
curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux.sh | sudo bash
```
Le script détecte le hostname automatiquement, installe Python3/pip si besoin, crée le service systemd et démarre l'agent.
