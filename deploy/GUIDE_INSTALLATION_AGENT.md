# 🚀 GUIDE DE DÉPLOIEMENT AGENT DASHFLEET

## 📋 ÉTAPE 1: Récupérer votre API Key

### Sur le VPS (83.150.218.175):
```bash
ssh root@83.150.218.175
cd /opt/dashfleet
sqlite3 data/fleet.db "SELECT key, org_id FROM api_keys WHERE revoked=0 LIMIT 1;"
```

**OU** via le dashboard web:
1. Allez sur https://dash-fleet.com/admin/tokens
2. Connectez-vous avec votre compte admin
3. Copiez une clé API existante ou créez-en une nouvelle

---

## 📋 ÉTAPE 2: Préparer les scripts

### Remplacez `VOTRE_API_KEY_ICI` dans les fichiers suivants:
- `deploy/install_windows_complete.ps1` (ligne 11)
- `deploy/install_linux_complete.sh` (ligne 10)

---

## 🪟 INSTALLATION SUR WINDOWS

### Méthode 1: PowerShell (Recommandé)
```powershell
# Télécharger le script
$url = "https://raw.githubusercontent.com/BunaTech-G/Dashboard-syst-me-/fix/pyproject-exclude/deploy/install_windows_complete.ps1"
Invoke-WebRequest -Uri $url -OutFile install_agent.ps1

# Exécuter en tant qu'Administrateur
.\install_agent.ps1 -ApiKey "votre_api_key_ici"
```

### Méthode 2: Copier le fichier local
```powershell
# Depuis C:\Users\SIDIBE\OneDrive\Bureau\DASH-FLEET\deploy\
# Copiez install_windows_complete.ps1 sur la machine cible

# Modifiez l'API key (ligne 11):
$ApiKey = "votre_api_key_réelle"

# Exécutez en tant qu'Administrateur:
.\install_windows_complete.ps1
```

### Vérifier l'installation:
```powershell
Get-ScheduledTask -TaskName "DashFleet Agent" | Get-ScheduledTaskInfo
Get-Content "C:\Program Files\DashFleet\logs\agent.log" -Tail 20
```

---

## 🐧 INSTALLATION SUR LINUX

### Méthode 1: Curl (Recommandé)
```bash
# Télécharger et exécuter en une commande
curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dashboard-syst-me-/fix/pyproject-exclude/deploy/install_linux_complete.sh | \
  sudo API_KEY="votre_api_key_ici" bash
```

### Méthode 2: Fichier local
```bash
# Copiez install_linux_complete.sh sur le serveur
# Modifiez l'API key (ligne 10):
API_KEY="${API_KEY:-votre_api_key_réelle}"

# Rendez le script exécutable et lancez:
chmod +x install_linux_complete.sh
sudo ./install_linux_complete.sh
```

### Vérifier l'installation:
```bash
systemctl status dashfleet-agent
journalctl -u dashfleet-agent -f
tail -f /opt/dashfleet-agent/logs/agent.log
```

---

## 🔧 PERSONNALISATION

### Changer l'intervalle de reporting:
**Windows:**
```powershell
.\install_windows_complete.ps1 -ApiKey "votre_key" -IntervalSeconds 60
```

**Linux:**
```bash
sudo INTERVAL_SECONDS=60 API_KEY="votre_key" bash install_linux_complete.sh
```

### Spécifier un Machine ID custom:
**Windows:**
```powershell
.\install_windows_complete.ps1 -ApiKey "votre_key" -MachineId "serveur-web-01"
```

**Linux:**
```bash
# Modifier le script ligne 58:
MACHINE_ID="serveur-web-01"
```

---

## 📊 VÉRIFICATION DANS LE DASHBOARD

1. Allez sur https://dash-fleet.com/
2. Connectez-vous
3. Cliquez sur "Fleet" dans le menu
4. Vos machines devraient apparaître dans les 30 secondes

---

## 🔍 DÉPANNAGE

### Problème: L'agent ne démarre pas

**Windows:**
```powershell
# Vérifier les logs
Get-Content "C:\Program Files\DashFleet\logs\agent.log"

# Vérifier la tâche planifiée
Get-ScheduledTask -TaskName "DashFleet Agent"

# Redémarrer manuellement
Start-ScheduledTask -TaskName "DashFleet Agent"
```

**Linux:**
```bash
# Vérifier les logs
journalctl -u dashfleet-agent -n 50

# Vérifier le fichier de log
cat /opt/dashfleet-agent/logs/agent.log

# Redémarrer
sudo systemctl restart dashfleet-agent
```

### Problème: "Unauthorized" dans les logs

**Solution:** Vérifiez que votre API key est correcte dans `config.json`

**Windows:** `C:\Program Files\DashFleet\config.json`
**Linux:** `/opt/dashfleet-agent/config.json`

---

## 📁 STRUCTURE D'INSTALLATION

### Windows:
```
C:\Program Files\DashFleet\
├── fleet_agent.py
├── fleet_utils.py
├── config.json
├── logs\
│   └── agent.log
└── .venv\
    └── Scripts\python.exe
```

### Linux:
```
/opt/dashfleet-agent/
├── fleet_agent.py
├── fleet_utils.py
├── config.json
├── logs/
│   └── agent.log
└── venv/
    └── bin/python
```

---

## 🔐 SÉCURITÉ

- ✅ L'API key est stockée localement dans `config.json`
- ✅ Les communications utilisent HTTPS vers `dash-fleet.com`
- ✅ L'agent tourne avec les privilèges SYSTEM (Windows) ou root (Linux)
- ✅ Aucune donnée sensible n'est transmise (seulement métriques système)

---

## 📝 EXEMPLE DE API KEY

Votre API key ressemble à ceci:
```
api_1234567890abcdef1234567890abcdef1234567890ab
```

**IMPORTANT:** Ne partagez jamais votre API key publiquement!

---

## ✅ CHECKLIST DE DÉPLOIEMENT

- [ ] Récupéré l'API key depuis le VPS ou dashboard
- [ ] Modifié les scripts avec la bonne API key
- [ ] Téléchargé les scripts sur les machines cibles
- [ ] Exécuté les scripts en tant qu'Administrateur/root
- [ ] Vérifié que les services sont actifs
- [ ] Vérifié l'apparition des machines dans le dashboard

---

**Besoin d'aide?** Consultez les logs ou contactez le support technique.
