# DashFleet Agent - Installation Rapide (All-in-One)

Installer l'agent DashFleet sur n'importe quel poste Windows **en une seule commande**.

## Prérequis
- Windows 10 / 11
- PowerShell (lancé en Administrateur)
- Accès Internet

## Installation (One-Liner)

### Méthode 1 : Directement depuis GitHub (recommandée)

Ouvre PowerShell **en Administrateur** et exécute :

```powershell
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_oneliner.ps1' -OutFile $env:TEMP\install.ps1 ; & $env:TEMP\install.ps1 -ApiKey 'd2f6f9a8-3c7e-4c1f-9b0f-123456789abc'"
```

Remplace `'d2f6f9a8-3c7e-4c1f-9b0f-123456789abc'` par ton **API Key** réelle.

### Méthode 2 : Personnalisé (nom de machine)

```powershell
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_oneliner.ps1' -OutFile $env:TEMP\install.ps1 ; & $env:TEMP\install.ps1 -ApiKey 'd2f6f9a8-3c7e-4c1f-9b0f-123456789abc' -MachineId 'server-01'"
```

### Méthode 3 : Copier-coller simple

1. Ouvre PowerShell **en Administrateur**
2. Copie-colle cette commande :
   ```powershell
   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_oneliner.ps1" -OutFile "$env:TEMP\install.ps1"; & "$env:TEMP\install.ps1" -ApiKey "d2f6f9a8-3c7e-4c1f-9b0f-123456789abc"
   ```

## Ce que fait le script

1. ✅ Vérifie les droits Administrateur
2. ✅ Crée les répertoires (C:\Program Files\DashFleet\ ou C:\DashFleet\)
3. ✅ **Télécharge l'EXE autonome** depuis GitHub (embarque Python + psutil + requests)
4. ✅ Génère `config.json` (UTF-8 sans BOM) avec ton token + hostname
5. ✅ Crée la tâche planifiée "DashFleet Agent" (SYSTEM, démarrage automatique)
6. ✅ Démarre l'agent immédiatement

## Vérifications après installation

### Voir le statut de la tâche
```powershell
Get-ScheduledTask -TaskName "DashFleet Agent"
```

### Voir les 10 derniers logs
```powershell
Get-Content "C:\DashFleet\logs\agent.log" -Tail 10
```

### Voir les machines sur le dashboard
```powershell
Invoke-RestMethod -Uri "https://dash-fleet.com/api/fleet/public" -Method Get | ConvertTo-Json
```

## Dashboard
Accès : https://dash-fleet.com/fleet

La machine apparaîtra dans les **30 secondes** après l'installation.

## Désinstallation

```powershell
Unregister-ScheduledTask -TaskName "DashFleet Agent" -Confirm:$false
Remove-Item "C:\DashFleet" -Recurse -Force
```

## Paramètres

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `-ApiKey` | Obligatoire | Clé d'authentification (token API) |
| `-MachineId` | `$env:COMPUTERNAME` | Nom de la machine (hostname réel du PC) |
| `-ServerUrl` | `https://dash-fleet.com` | URL du serveur DashFleet |
| `-Interval` | `30` | Intervalle d'envoi en secondes |

## Exemples

### Installation sur plusieurs postes (script distribuable)

Crée un fichier `install.ps1` local :

```powershell
@"
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_oneliner.ps1' -OutFile \$env:TEMP\install.ps1 ; & \$env:TEMP\install.ps1 -ApiKey 'd2f6f9a8-3c7e-4c1f-9b0f-123456789abc'"
"@ | Out-File -FilePath "C:\install_dashfleet.ps1" -Encoding ASCII
```

Puis distribue `C:\install_dashfleet.ps1` sur les postes et exécute-le.

## Linux

Pour Linux (Kali, Debian, Ubuntu) :

```bash
curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux.sh | sudo bash
```

Le script installe Python3/pip automatiquement et crée un service systemd.

## Support

- Logs : `C:\DashFleet\logs\agent.log`
- Config : `C:\DashFleet\config.json`
- Service : Tâche planifiée "DashFleet Agent"
