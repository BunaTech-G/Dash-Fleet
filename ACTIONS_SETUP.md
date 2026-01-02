# Actions - Configuration et Dépannage

## Problème : Les actions (Envoyer Message, Redémarrer) ne fonctionnent pas

### Cause
Les actions requièrent une clé API Bearer token d'une organisation (`org_id`).

### Solution

#### 1. Obtenez votre clé API

```bash
# On the VPS:
cd /opt/dashfleet
sqlite3 data/fleet.db "SELECT key FROM api_keys WHERE org_id='org_default' AND revoked=0 LIMIT 1;"
```

**Résultat attendu:** `api_xxxxxxxxxxxxxxxxxx`

#### 2. Enregistrez la clé dans le navigateur

Sur https://dash-fleet.com/fleet, ouvrez la Console (F12) et exécutez:

```javascript
localStorage.setItem('auth_token', 'api_xxxxxxxxxxxxxxxxxx');
window.location.reload();
```

#### 3. Testez une action

- Cliquez sur **💬 Envoyer Message** sur une machine
- Entrez votre message
- Cliquez **✓ Envoyer**

Vous devriez voir un toast vert ✅

### Diagnostic

Si ça ne fonctionne toujours pas:

```bash
# Check agent logs for action errors
ssh root@83.150.218.175 "tail -20 /opt/dashfleet/logs/api.log | grep -i action"

# Test API directly
curl -X POST https://dash-fleet.com/api/actions/queue \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer api_xxxxxxxxxxxxxxxxxx" \
  -d '{
    "machine_id": "kclient1",
    "action_type": "message",
    "data": {"message": "test"}
  }'
```

### Permanent Fix (for future installations)

Le script `scripts/init_api_keys.sh` crée automatiquement une clé API pour `org_default` au déploiement.

### Types d'actions supportées

- **message** : Envoyer un message notification
- **restart** : Redémarrer l'agent
- **reboot** : Redémarrer la machine complète

### Architecture

```
Dashboard UI
    ↓ (Bearer Token from localStorage)
/api/actions/queue (requires org_id auth)
    ↓
SQLite actions table
    ↓
Agent /api/actions/pending (polls every 30s)
    ↓
Action execution on machine
    ↓
POST /api/actions/report (result)
```
