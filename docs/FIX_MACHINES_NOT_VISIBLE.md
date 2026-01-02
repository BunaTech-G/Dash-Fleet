# 🔧 Fix: Machines pas visibles dans DashFleet

## Problème identifié

Les machines ne sont pas visibles car **l'authentification API est manquante**.

Le dashboard utilise `/api/fleet` qui nécessite un Bearer token (clé API).

## Solution rapide

### Option 1: Utiliser la page de connexion

1. **Ouvrir la page de connexion**: https://dash-fleet.com/fleet/login
2. **Entrer une clé API valide** (ex: `d2f6f9a8-3c7e-4c1f-9b0f-123456789abc`)
3. **Cliquer sur "Se connecter"**
4. **Redirection automatique** vers le dashboard avec les machines visibles

### Option 2: Console du navigateur

1. **Ouvrir le dashboard**: https://dash-fleet.com/fleet
2. **Appuyer sur F12** pour ouvrir la console
3. **Exécuter la commande**:
   ```javascript
   sessionStorage.setItem('api_key', 'd2f6f9a8-3c7e-4c1f-9b0f-123456789abc');
   location.reload();
   ```
4. **Les machines apparaissent** après rechargement

### Option 3: Obtenir une nouvelle clé API

```bash
# Se connecter au VPS
ssh root@83.150.218.175

# Créer une nouvelle organisation
cd /opt/dashfleet
python3 scripts/create_org.sh "Mon Organisation"

# Output:
# ✅ Organization created: org_xxx
# 🔑 API Key: api_yyy (copier cette clé)
```

## Vérification

### Tester l'API avec PowerShell

```powershell
# Avec clé API
$apiKey = "d2f6f9a8-3c7e-4c1f-9b0f-123456789abc"
$headers = @{ "Authorization" = "Bearer $apiKey" }
Invoke-RestMethod -Uri "https://dash-fleet.com/api/fleet" -Headers $headers | ConvertTo-Json -Depth 5

# Output attendu:
# {
#   "count": 1,
#   "data": [
#     {
#       "id": "wclient2",
#       "machine_id": "wclient2",
#       "cpu_percent": 38.7,
#       "ram_percent": 77.5,
#       "disk_percent": 98.9,
#       ...
#     }
#   ],
#   "expired": []
# }
```

### Vérifier que le serveur VPS fonctionne

```bash
# Sur le VPS
systemctl status dashfleet
# Output: Active: active (running)

# Vérifier les logs
tail -f /opt/dashfleet/logs/api.log
```

### Vérifier les données en base

```bash
# Sur le VPS
cd /opt/dashfleet
python3 check_db.py  # Nouveau script de diagnostic
```

## Diagnostic complet

### État actuel confirmé

✅ **VPS fonctionnel** (83.150.218.175)
✅ **API disponible** (https://dash-fleet.com/api/fleet/public)
✅ **1 machine visible** (`wclient2` dans `org_default`)
✅ **Gunicorn actif** (3 workers sur 127.0.0.1:5000)
✅ **Nginx reverse proxy** (HTTPS Let's Encrypt)

❌ **Dashboard sans authentification** → Les machines ne s'affichent pas
❌ **sessionStorage.api_key manquante** → Requêtes en 403 Unauthorized

## Commandes de déploiement

### Pousser les changements sur le VPS

```powershell
# Depuis votre PC Windows
git add main.py templates/fleet_login.html check_db.py inspect_report.py
git commit -m "feat: Add fleet login page and diagnostic tools"
git push origin fix/pyproject-exclude
```

### Déployer sur le VPS

```bash
# SSH sur le VPS
ssh root@83.150.218.175

# Tirer les changements
cd /opt/dashfleet
git pull origin fix/pyproject-exclude

# Redémarrer le service
systemctl restart dashfleet

# Vérifier
systemctl status dashfleet
curl -I https://dash-fleet.com/fleet/login
# Output: HTTP/2 200
```

## Résumé

Le problème n'était **pas** un bug dans le code, mais un **manque d'authentification** dans le navigateur.

**Solution**: Utiliser `/fleet/login` pour stocker une clé API valide dans `sessionStorage`.

---

**Créé le**: 2026-01-02  
**Auteur**: DashFleet Diagnostic Tool
