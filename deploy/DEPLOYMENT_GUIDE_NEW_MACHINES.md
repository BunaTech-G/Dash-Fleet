# Guide de Déploiement DashFleet Agent pour Chaque Nouvelle Machine

## 🚀 Déploiement Rapide (1 commande)

### Option 1: Avec PowerShell (RECOMMANDÉ)

```powershell
# En tant qu'administrateur:
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\deploy\setup_scheduled_task.ps1" `
  -ApiKey "api_a7ee4957ca1640e180802c256fdf" `
  -MachineId "OSIDIBE-PC"
```

### Option 2: Télécharger depuis GitHub et exécuter

```powershell
# En tant qu'administrateur:
$ScriptPath = "$env:TEMP\setup_dashfleet.ps1"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/setup_scheduled_task.ps1" -OutFile $ScriptPath
& $ScriptPath -ApiKey "api_a7ee4957ca1640e180802c256fdf" -MachineId "NOMDELAMACHINE"
```

---

## 📋 Pré-requis

1. **Windows 7 ou plus récent**
2. **Droits administrateur** sur la machine
3. **Accès internet** pour télécharger l'agent
4. **API Key valide** depuis le serveur DashFleet (https://dash-fleet.com)

---

## 🔑 Obtenir une Clé API

### Si vous êtes administrateur du serveur DashFleet:

```bash
ssh root@83.150.218.175
cd /opt/dashfleet

# Générer une nouvelle clé API
python3 << 'EOF'
import sqlite3
import uuid
import time

conn = sqlite3.connect('data/fleet.db')
c = conn.cursor()

# Créer une nouvelle organisation
org_id = 'prod-' + str(uuid.uuid4())[:8]
api_key = 'api_' + str(uuid.uuid4()).replace('-', '')[:28]

c.execute('INSERT INTO organizations (id, name) VALUES (?, ?)', (org_id, 'Production'))
c.execute('INSERT INTO api_keys (key, org_id, created_at, revoked) VALUES (?, ?, ?, 0)',
          (api_key, org_id, time.time()))
conn.commit()

print(f'API_KEY={api_key}')
EOF
```

Copier la clé API affichée.

---

## 🛠️ Étapes Manuelles de Configuration

Si vous préférez configurer manuellement:

### 1. Télécharger l'agent

```powershell
# Créer le dossier d'installation
mkdir "C:\Program Files\DashFleet" -ErrorAction SilentlyContinue

# Télécharger l'agent
$DownloadURL = "https://github.com/BunaTech-G/Dash-Fleet/raw/fix/pyproject-exclude/deploy/agent_binaries/fleet_agent.exe"
Invoke-WebRequest -Uri $DownloadURL -OutFile "C:\Program Files\DashFleet\dashfleet-agent.exe"
```

### 2. Créer le fichier de configuration

```powershell
$Config = @{
    server = "https://dash-fleet.com"
    path = "/api/fleet/report"
    token = "API_KEY_ICI"          # ← Remplacer par votre clé API
    interval = 30
    machine_id = "NOM_MACHINE"      # ← Remplacer par le nom de la machine
    log_file = "C:\Program Files\DashFleet\logs\agent.log"
} | ConvertTo-Json

$Config | Out-File -FilePath "C:\Program Files\DashFleet\config.json" -Encoding UTF8 -Force
```

### 3. Créer la tâche planifiée

```powershell
# Exécuter en tant qu'administrateur:

$TaskName = "DashFleet Agent"
$AgentPath = "C:\Program Files\DashFleet\dashfleet-agent.exe"
$ConfigPath = "C:\Program Files\DashFleet\config.json"

# Supprimer la tâche existante si elle existe
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Créer une nouvelle tâche
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Action = New-ScheduledTaskAction -Execute $AgentPath -Argument "--config `"$ConfigPath`""
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -RunLevel Highest

# Démarrer l'agent
Start-ScheduledTask -TaskName $TaskName
```

---

## ✅ Vérification du Déploiement

### 1. Vérifier la tâche planifiée

```powershell
Get-ScheduledTask -TaskName "DashFleet Agent" | Select-Object TaskName, State
```

**Résultat attendu:**
```
TaskName            State
--------            -----
DashFleet Agent     Ready
```

### 2. Vérifier les logs

```powershell
# Attendre 30-60 secondes, puis:
Get-Content "C:\Program Files\DashFleet\logs\agent.log" -Tail 10
```

**Résultat attendu:**
```
Agent démarré -> https://dash-fleet.com/api/fleet/report
[HH:MM:SS] OK HTTP 200 | CPU X% RAM Y% Disk Z% | Score XX/100
```

### 3. Vérifier sur le dashboard

Accéder à: **https://dash-fleet.com/fleet/public**

Votre machine doit apparaître avec ses métriques en temps réel.

---

## 🔄 Déploiement par Batch (Plusieurs Machines)

Créer un script batch pour déployer sur plusieurs machines:

```powershell
# machines.csv
# MachineId,ApiKey
# MACHINE-01,api_xxxx
# MACHINE-02,api_yyyy

$Machines = Import-Csv "machines.csv"

foreach ($Machine in $Machines) {
    Write-Host "Déploiement sur $($Machine.MachineId)..." -ForegroundColor Cyan
    
    $DownloadURL = "https://github.com/BunaTech-G/Dash-Fleet/raw/fix/pyproject-exclude/deploy/setup_scheduled_task.ps1"
    $ScriptPath = "$env:TEMP\setup_dashfleet.ps1"
    
    Invoke-WebRequest -Uri $DownloadURL -OutFile $ScriptPath
    
    & $ScriptPath -ApiKey $Machine.ApiKey -MachineId $Machine.MachineId
    
    Start-Sleep -Seconds 5
}

Write-Host "Déploiement complet!" -ForegroundColor Green
```

---

## 🐛 Dépannage

### Problème: Agent ne démarre pas

```powershell
# Vérifier l'état de la tâche
Get-ScheduledTask -TaskName "DashFleet Agent" | Get-ScheduledTaskInfo

# Redémarrer manuellement
Start-ScheduledTask -TaskName "DashFleet Agent"

# Vérifier les logs
Get-Content "C:\Program Files\DashFleet\logs\agent.log" -Tail 20
```

### Problème: Clé API invalide

Vérifier que la clé API:
1. Commence par `api_`
2. Existe sur le serveur DashFleet
3. N'est pas révoquée

### Problème: Machine n'apparaît pas sur le dashboard

1. Attendre 30-60 secondes (délai de synchronisation)
2. Vérifier que l'agent s'exécute: `Get-ScheduledTask -TaskName "DashFleet Agent"`
3. Vérifier la connexion internet
4. Vérifier les logs pour les erreurs

---

## 📝 Paramètres Avancés

### Configurer l'intervalle d'envoi

Par défaut: 30 secondes

```powershell
# Pour changer à 60 secondes:
& setup_scheduled_task.ps1 -ApiKey "..." -MachineId "..." -Interval 60
```

### Personnaliser le chemin de log

```powershell
& setup_scheduled_task.ps1 -ApiKey "..." -MachineId "..." -LogPath "C:\Logs\dashfleet.log"
```

### Utiliser un serveur personnalisé

```powershell
& setup_scheduled_task.ps1 -ApiKey "..." -MachineId "..." -Server "https://dashfleet.example.com"
```

---

## 📊 Dashboard

Une fois déployé, voir les métriques sur:
- **Dashboard Public**: https://dash-fleet.com/fleet/public
- **Dashboard Authentifié**: https://dash-fleet.com/fleet (avec authentification)

---

## 🔒 Sécurité

- Les clés API sont stockées en local dans: `C:\Program Files\DashFleet\config.json`
- L'agent s'exécute avec les droits **SYSTEM**
- La communication est en **HTTPS**
- Les logs sont locaux: `C:\Program Files\DashFleet\logs\agent.log`

---

## 📞 Support

Pour toute question ou problème:
1. Vérifier les logs locaux
2. Vérifier la connexion internet
3. Vérifier la validité de la clé API
4. Consulter le github: https://github.com/BunaTech-G/Dash-Fleet

---

**Dernière mise à jour**: 2 janvier 2026
