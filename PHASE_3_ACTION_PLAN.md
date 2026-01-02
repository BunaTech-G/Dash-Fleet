# 🎯 PLAN D'ACTION IMMÉDIAT - Phase 3 Corrections Critiques

**Date:** 2 janvier 2026  
**Objectif:** Corriger 5 problèmes critiques identifiés dans l'audit  
**Durée estimée:** 4-5 heures  
**Priorité:** 🔴 URGENTE  

---

## Résumé des Problèmes à Résoudre

| # | Problème | Sévérité | Temps | Fix |
|---|----------|----------|-------|-----|
| 1 | FLEET_TTL_SECONDS = 600 (vs 86400) | 🔴 CRITIQUE | 5 min | Change constant |
| 2 | /api/fleet/public expose all orgs | 🔴 CRITIQUE | 20 min | Require Bearer token |
| 3 | TTL hardcoded frontend (mismatch) | 🔴 CRITIQUE | 30 min | Add /api/config endpoint |
| 4 | No OS/version metadata | 🟠 MAJEUR | 1h | Add platform.system() to agent |
| 5 | No heartbeat endpoint | 🟠 MAJEUR | 1h | Add /api/fleet/ping endpoint |
| **Total** | | | **3-4 heures** | |

---

## Action 1: Fix FLEET_TTL_SECONDS (5 minutes) 🔴 CRITIQUE

### Problème
```python
# constants.py (actuellement)
FLEET_TTL_SECONDS = 600  # 10 minutes ❌

# fleet.html (actuellement)
const FLEET_TTL = 86400;  // 24 hours ❌

# Résultat: Désynchronisation → machines disparaissent en backend mais restent en dashboard
```

### Solution
```bash
# Fichier: constants.py
# Ligne: 13

# AVANT:
FLEET_TTL_SECONDS = 600

# APRÈS:
FLEET_TTL_SECONDS = 86400  # 24 hours (must match frontend)
```

### Vérification
```bash
# After change:
grep "FLEET_TTL" constants.py     # Should show 86400
grep "FLEET_TTL =" fleet.html     # Already shows 86400
```

### Impact
- ✅ Machines remain visible for 24h
- ✅ Synchronized with frontend
- ✅ No more disappearing machines

---

## Action 2: Secure /api/fleet/public (20 minutes) 🔴 CRITIQUE

### Problème
```python
# Actuellement: /api/fleet/public retourne ALL organizations
# Zero authentication required
# BREACH DE CONFIDENTIALITÉ MULTI-TENANT

@app.route("/api/fleet/public")
def api_fleet_public():
    # Returns ALL FLEET_STATE (all orgs!)
    data = list(FLEET_STATE.values())  # ❌ No org_id filtering
    return jsonify({"count": len(data), "data": data})
```

### Solution (Approche A: Require Bearer Token - RECOMMANDÉE)

**Fichier: main.py**  
**Ligne: ~1390**

```python
# AVANT (lignes 1390-1406):
@app.route("/api/fleet/public")
def api_fleet_public():
    # Public version: return all machines (no auth required)
    now_ts = time.time()
    expired = []
    for mid, entry in list(FLEET_STATE.items()):
        if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS:
            expired.append(entry.get("id") or mid)
            FLEET_STATE.pop(mid, None)

    if expired:
        _save_fleet_state()

    data = list(FLEET_STATE.values())
    return jsonify({"count": len(data), "expired": expired, "data": data})

# APRÈS:
@app.route("/api/fleet/public")
def api_fleet_public():
    """Public fleet endpoint - requires Bearer token (org-scoped)."""
    ok, org_id = _check_org_key()
    if not ok or not org_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Purge expired entries for this org only
    now_ts = time.time()
    expired = []
    for mid, entry in list(FLEET_STATE.items()):
        if entry.get("org_id") != org_id:
            continue
        if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS:
            expired.append(entry.get("id") or mid)
            FLEET_STATE.pop(mid, None)

    if expired:
        _save_fleet_state()

    # Return only this org's machines
    data = [v for v in FLEET_STATE.values() if v.get("org_id") == org_id]
    return jsonify({"count": len(data), "expired": expired, "data": data})
```

### Alternative B: Return Empty (More Secure)
```python
@app.route("/api/fleet/public")
def api_fleet_public():
    """Public endpoint - deprecated, use /api/fleet instead."""
    return jsonify({"error": "Use /api/fleet instead"}), 410
```

### Vérification
```bash
# BEFORE: Can see all orgs without token
curl http://localhost:5000/api/fleet/public
# Returns: {"count": 50, "data": [...all machines...]}

# AFTER: Requires Bearer token
curl http://localhost:5000/api/fleet/public
# Returns: {"error": "Unauthorized"}

# With correct token
curl -H "Authorization: Bearer api_xxx" http://localhost:5000/api/fleet/public
# Returns: {"count": 3, "data": [...org-scoped machines...]}
```

### Impact
- ✅ Multi-tenant security restored
- ✅ Only authenticated users see org data
- ✅ Dashboard still works (already uses Bearer token)
- ⚠️ Need to update any public dashboards (if they exist)

---

## Action 3: Synchronize TTL Config (30 minutes) 🔴 CRITIQUE

### Problème
```javascript
// fleet.html (hardcoded)
const FLEET_TTL = 86400;  // If you change it in backend, you MUST update frontend too

// Problem: Two sources of truth = easy to desynchronize
```

### Solution: New /api/config Endpoint

**Fichier: main.py**

**Ajouter après @app.route("/api/status"):**

```python
@app.route("/api/config")
@limiter.limit("100/minute")
def api_config():
    """Return configuration that frontend needs."""
    return jsonify({
        "FLEET_TTL_SECONDS": FLEET_TTL_SECONDS,
        "REFRESH_INTERVAL_MS": 5000,
        "API_VERSION": "1.0.0",
        "FEATURES": {
            "messaging": False,  # Will enable in Phase X
            "commands": False,
            "heartbeat": False,  # Will enable with heartbeat endpoint
        }
    })
```

**Fichier: templates/fleet.html**

**Au début du script (après les commentaires):**

```html
<script>
// ===== LOAD CONFIG FROM SERVER =====
let FLEET_TTL = 86400;  // Default fallback
let REFRESH_INTERVAL = 5000;  // Default fallback

fetch('/api/config')
  .then(r => r.json())
  .then(config => {
    // Update from server config
    FLEET_TTL = config.FLEET_TTL_SECONDS;
    REFRESH_INTERVAL = config.REFRESH_INTERVAL_MS;
    
    console.log(`Fleet TTL: ${FLEET_TTL}s, Refresh: ${REFRESH_INTERVAL}ms`);
    
    // Adjust refresh interval if needed
    const SKELETON_COUNT = 4;
    
    // ... rest of existing code ...
  })
  .catch(err => {
    console.warn('Could not load config, using defaults', err);
    // Continue with hardcoded defaults
  });

// ===== CONFIGURATION =====
// These are now loaded from /api/config above
// const FLEET_TTL = 86400;  // REMOVE THIS LINE - loaded from config
// const REFRESH_INTERVAL = 5000;  // REMOVE THIS LINE - loaded from config
const SKELETON_COUNT = 4;
// ... rest of existing code ...
</script>
```

### Vérification
```bash
# Test endpoint
curl http://localhost:5000/api/config | python -m json.tool
# {
#   "FLEET_TTL_SECONDS": 86400,
#   "REFRESH_INTERVAL_MS": 5000,
#   "API_VERSION": "1.0.0",
#   "FEATURES": { ... }
# }

# Browser console should show:
# Fleet TTL: 86400s, Refresh: 5000ms
```

### Impact
- ✅ No more hardcoding TTL in frontend
- ✅ Change TTL once in backend, frontend picks it up
- ✅ Can add new feature flags (messaging, commands)
- ✅ Can adjust refresh interval remotely

---

## Action 4: Add OS/Version Metadata (1 hour) 🟠 MAJEUR

### Problème
```python
# Actuellement: Agent ne collecte que metrics
# Missing:  OS, OS version, Python version, agent version, hardware ID
# Impact: Dashboard can't filter by OS, can't track versions
```

### Solution: Enhance collect_agent_stats()

**Fichier: fleet_agent.py**

**Au début du fichier (après imports):**

```python
import platform
import uuid
```

**Remplacer la fonction collect_agent_stats():**

```python
def collect_agent_stats() -> dict:
    """Collecte les métriques système principales et les retourne sous forme de dict."""
    cpu_percent = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor or "/")
    uptime_seconds = time.time() - psutil.boot_time()

    stats = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cpu_percent": float(cpu_percent),
        "ram_percent": float(ram.percent),
        "ram_used_gib": float(format_bytes_to_gib(ram.used)),
        "ram_total_gib": float(format_bytes_to_gib(ram.total)),
        "disk_percent": float(disk.percent),
        "disk_used_gib": float(format_bytes_to_gib(disk.used)),
        "disk_total_gib": float(format_bytes_to_gib(disk.total)),
        "uptime_seconds": float(uptime_seconds),
        "uptime_hms": format_uptime_hms(uptime_seconds),
        
        # NEW: System information
        "system": {
            "os": platform.system(),              # "Windows", "Linux", "Darwin"
            "os_version": platform.release(),     # "10.0.19045" or "5.10.0"
            "platform": platform.platform(),      # Full platform string
            "architecture": platform.machine(),   # "x86_64", "ARM64", etc.
            "python_version": platform.python_version(),  # "3.11.0"
            "hardware_id": hex(uuid.getnode()),   # MAC address as UUID
        }
    }
    
    stats["health"] = calculate_health_score(stats)
    
    # Validation simple des métriques
    for k in ("cpu_percent", "ram_percent", "disk_percent"):
        if not isinstance(stats[k], (int, float)):
            stats[k] = 0.0
    
    return stats
```

### Vérification
```bash
# Test agent locally
python fleet_agent.py --server http://localhost:5000 --token test --machine-id test-pc

# Should now show:
# 2026-01-02 15:30:45 OK HTTP 200 | CPU 45.2% RAM 62.1% Disk 34.5% | Score 78/100 | OS Windows
```

### Mise à jour Schema

**Fichier: schemas.py**

**Mettre à jour MetricsSchema:**

```python
class MetricsSchema(Schema):
    """Validates individual metric fields in a report."""
    cpu_percent = fields.Float(required=True)
    ram_percent = fields.Float(required=True)
    disk_percent = fields.Float(required=True)
    timestamp = fields.Str(required=False)
    ram_used_gib = fields.Float(required=False)
    ram_total_gib = fields.Float(required=False)
    disk_used_gib = fields.Float(required=False)
    disk_total_gib = fields.Float(required=False)
    uptime_seconds = fields.Float(required=False)
    uptime_hms = fields.Str(required=False)
    health = fields.Dict(required=False)
    
    # NEW: System information
    system = fields.Dict(required=False)  # Allows system.os, system.os_version, etc.
```

### Impact
- ✅ Dashboard can filter by OS (Windows vs Linux)
- ✅ Can track agent/Python versions
- ✅ Hardware ID allows unique machine identification
- ✅ +~200 bytes per report (negligible)

---

## Action 5: Add Heartbeat Endpoint (1 hour) 🟠 MAJEUR

### Problème
```python
# Actuellement: Agent envoie metrics toutes les 30s
# Si agent crash mais network ok: API pense agent is ok
# Si agent ok mais network down: API pense agent is down
# Solution: Lightweight heartbeat pour tester connectivity
```

### Solution: New Ping Endpoint

**Fichier: main.py**

**Ajouter après /api/status endpoint:**

```python
@app.route("/api/fleet/ping", methods=["POST"])
@limiter.limit("120/minute")  # 2 per second max per agent
def api_fleet_ping():
    """
    Lightweight agent heartbeat endpoint.
    
    Agents send lightweight ping to confirm connectivity.
    No metrics, just confirmation that agent is alive.
    """
    ok, org_id = _check_org_key()
    if not ok or not org_id:
        logging.warning(f"Heartbeat failed: invalid org_key from {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        payload = request.get_json(force=True)
        machine_id = payload.get("machine_id", "unknown")
        hardware_id = payload.get("hardware_id")
        timestamp = payload.get("timestamp", time.time())
    except Exception as e:
        logging.error(f"Heartbeat parse error: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    
    try:
        store_key = f"{org_id}:{machine_id}"
        
        # Update heartbeat timestamp
        if store_key in FLEET_STATE:
            FLEET_STATE[store_key]["last_ping"] = time.time()
            FLEET_STATE[store_key]["status"] = "online"
        else:
            # First time seeing this machine via heartbeat
            FLEET_STATE[store_key] = {
                "id": machine_id,
                "machine_id": machine_id,
                "org_id": org_id,
                "last_ping": time.time(),
                "status": "online",
                "report": {}  # Empty report until first metrics
            }
        
        _save_fleet_state()
        
        logging.info(f"Heartbeat received from {machine_id} ({org_id})")
        
        return jsonify({
            "ok": True,
            "timestamp": time.time(),
            "server_time_offset": time.time() - timestamp  # Clock skew detection
        })
    
    except Exception as e:
        logging.error(f"Heartbeat processing error: {e}")
        return jsonify({"error": str(e)}), 500
```

### Agent-Side Update

**Fichier: fleet_agent.py**

**Ajouter fonction:**

```python
def send_heartbeat(url: str, token: str, machine_id: str, hardware_id: str) -> bool:
    """Send lightweight heartbeat ping (no metrics)."""
    payload = {
        "machine_id": machine_id,
        "hardware_id": hardware_id,
        "timestamp": time.time()
    }
    data = json.dumps(payload).encode("utf-8")
    url_ping = url.rstrip("/") + "/api/fleet/ping"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url_ping, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            ok = 200 <= resp.getcode() < 300
            return ok
    except Exception as e:
        logging.debug(f"Heartbeat failed: {e}")
        return False
```

**Dans main(), modifier la boucle:**

```python
# In main loop, after reporting metrics, send heartbeat every 5th cycle
# (metrics every 10s, heartbeat every 50s)

import uuid as uuid_module

hardware_id = hex(uuid_module.getnode())

cycle = 0
while True:
    report = collect_agent_stats()
    ok, msg = post_report(url, token, machine_id, report)
    
    # Every 5 cycles, also send heartbeat
    cycle += 1
    if cycle % 5 == 0:
        hb_ok = send_heartbeat(server, token, machine_id, hardware_id)
    
    # ... rest of loop ...
    time.sleep(max(1.0, interval))
```

### Vérification
```bash
# Test heartbeat
curl -X POST http://localhost:5000/api/fleet/ping \
  -H "Authorization: Bearer api_xxx" \
  -H "Content-Type: application/json" \
  -d '{"machine_id":"test-pc","hardware_id":"aabbccddeeff","timestamp":1704267045}'

# Response:
# {"ok": true, "timestamp": 1704267045.123, "server_time_offset": 0.042}
```

### Impact
- ✅ Can distinguish "agent down" from "API down"
- ✅ Lightweight (< 200 bytes per heartbeat)
- ✅ Can detect clock skew
- ✅ Dashboard shows "last_ping" time
- ✅ Set heartbeat interval to avoid spam (every 30-60s)

---

## Résumé des Changements

### Fichiers à Modifier (5 fichiers)

```
1. constants.py (1 ligne)
   - Change FLEET_TTL_SECONDS from 600 to 86400

2. main.py (40-50 lignes)
   - Add /api/config endpoint
   - Secure /api/fleet/public
   - Add /api/fleet/ping endpoint

3. schemas.py (5 lignes)
   - Add system field to MetricsSchema

4. fleet_agent.py (60-80 lignes)
   - Add platform/uuid imports
   - Update collect_agent_stats() with system info
   - Add send_heartbeat() function
   - Update main loop to send heartbeat

5. templates/fleet.html (30-40 lignes)
   - Load config from /api/config
   - Remove hardcoded FLEET_TTL
   - Update authorization headers for /api/fleet
```

### Total Impact
- **Lines Changed:** ~150-200 total
- **Time Estimate:** 3-4 hours
- **Risk Level:** LOW (backward compatible)
- **Testing Required:** Unit tests + integration tests

---

## Checklist d'Exécution

### Avant de Commencer
- [ ] Créer une branche feature: `git checkout -b phase3-critical-fixes`
- [ ] Lire TECHNICAL_AUDIT.md au complet
- [ ] Sauvegarder config actuelle

### Phase 1: TTL Fix (5 min)
- [ ] Edit constants.py
- [ ] Test locally
- [ ] Commit: "Fix FLEET_TTL_SECONDS = 86400"

### Phase 2: Security Fix (20 min)
- [ ] Edit /api/fleet/public endpoint
- [ ] Test without token (should fail)
- [ ] Test with correct token (should work)
- [ ] Commit: "Secure /api/fleet/public - require Bearer token"

### Phase 3: Config Sync (30 min)
- [ ] Add /api/config endpoint
- [ ] Update fleet.html to load config
- [ ] Test config endpoint
- [ ] Test frontend loads correct TTL
- [ ] Commit: "Add /api/config endpoint for dynamic config"

### Phase 4: System Info (1h)
- [ ] Add imports to fleet_agent.py
- [ ] Update collect_agent_stats()
- [ ] Update MetricsSchema
- [ ] Test agent output includes system info
- [ ] Commit: "Add OS/version metadata to agent metrics"

### Phase 5: Heartbeat (1h)
- [ ] Add /api/fleet/ping endpoint
- [ ] Add send_heartbeat() to agent
- [ ] Update main loop
- [ ] Test heartbeat endpoint
- [ ] Test agent sends heartbeats
- [ ] Commit: "Add heartbeat endpoint for connectivity check"

### Après Exécution
- [ ] Run all tests: `pytest tests/unit/`
- [ ] Test full agent→API→dashboard flow
- [ ] Check git history: `git log --oneline -5`
- [ ] Merge to main: `git checkout main && git merge phase3-critical-fixes`
- [ ] Push to production
- [ ] Verify on VPS

---

## Points de Vigilance

### ⚠️ Backward Compatibility
- `/api/fleet/public` now requires Bearer token
- Any client using it without token WILL break
- Solution: Update docs, add migration guide

### ⚠️ Database Consistency
- Don't need DB migration (all changes are in-memory or config)
- Fleet data will persist normally

### ⚠️ Agent Version Mismatch
- Old agents will still work (heartbeat optional)
- New agents will send extra heartbeat traffic
- Mix of old/new agents is safe

### ✅ Rollback Plan
```bash
# If something breaks:
git reset --hard <previous-commit>
systemctl restart dashfleet
# OR on VPS:
cd /opt/dashfleet && git checkout main
systemctl restart dashfleet
```

---

**Status: Ready for Implementation** ✅

Next step: Implement these 5 fixes, then move to Phase 4 (optional: messages/actions).
