# DashFleet AI Agent Instructions

## Architecture Overview

DashFleet is a **multi-tenant fleet monitoring system** with three core components:

1. **Flask Backend** (`main.py`) - API server handling metrics, authentication, and multi-org data
2. **Python Agents** (`fleet_agent.py`) - Lightweight system monitors deployed on client machines
3. **SQLite Database** (`data/fleet.db`) - Multi-tenant schema with organizations, API keys, fleet data

**Data Flow**: Agent → POST `/api/fleet/report` (Bearer auth) → SQLite persistence → Dashboard UI fetches via `/api/fleet` or `/api/fleet/public`

## Critical Project-Specific Patterns

### Multi-Tenant Architecture
- All fleet data is scoped by `org_id` (from `api_keys` table)
- API authentication: Bearer token extracted from `api_keys` table via `_check_org_key()`
- Legacy `FLEET_TOKEN` env var supported for backward compatibility (deprecated)
- Database schema: `organizations` → `api_keys` → `fleet` (foreign keys enforce boundaries)

### Centralized Utilities (NEW - Jan 2026 Refactor)
Recent refactoring extracted duplicated code into shared modules:
- `fleet_utils.py` - Shared health calculations, formatting (health_score, bytes→GiB, uptime)
- `constants.py` - Configuration constants (thresholds, rate limits, paths)
- `logging_config.py` - Centralized logging setup

**Import Pattern**: Main app and agents both import from `fleet_utils`. Backward-compatible wrappers exist in `main.py` (e.g., `_health_score()` → `calculate_health_score()`).

### Health Score Algorithm
```python
# Core logic in fleet_utils.calculate_health_score()
# CPU: 100% → 0 score (linear from 50%)
# RAM: 100% → 0 score (linear from 60%)
# Disk: 100% → 0 score (linear from 70%)
# Weighted: CPU 35%, RAM 35%, Disk 30%
# Status: ≥80 = "ok", ≥60 = "warn", <60 = "critical"
```

### Authentication Workflow
```python
# In main.py endpoints:
ok, org_id = _check_org_key()  # Extracts Bearer token, validates against DB
if not ok:
    return jsonify({"error": "Unauthorized"}), 403
# All queries filtered by org_id
```

### Agent Configuration
Agents read `config.json` (JSON format) with:
```json
{
  "server": "https://dash-fleet.com",
  "path": "/api/fleet/report",
  "token": "api_xxx",  // From api_keys table
  "interval": 30,
  "machine_id": "hostname",
  "log_file": "logs/agent.log"
}
```

## Development Workflows

### Local Development
```powershell
# Activate venv (PowerShell)
.\.venv\Scripts\Activate.ps1

# Set secrets
$env:SECRET_KEY="random_hex"
$env:FLEET_TOKEN="legacy_token"  # Optional

# Run server
python main.py --web --host localhost --port 5000

# Run agent (separate terminal)
python fleet_agent.py --server http://localhost:5000 --token api_xxx --machine-id test-pc
```

### Production Deployment (VPS: 83.150.218.175)
```bash
# On VPS (/opt/dashfleet)
cd /opt/dashfleet
git pull origin fix/pyproject-exclude  # Current branch
systemctl restart dashfleet  # Gunicorn service
systemctl status dashfleet
tail -f logs/api.log
```

**Gunicorn Config**: 3 workers, binds to `127.0.0.1:5000`, proxied by Nginx (HTTPS via Let's Encrypt)

### Database Access
```bash
# On VPS
sqlite3 data/fleet.db
# List orgs: SELECT * FROM organizations;
# List keys: SELECT key, org_id FROM api_keys WHERE revoked=0;
# View fleet: SELECT * FROM fleet WHERE org_id='org_xxx';
```

### Testing
```powershell
# Syntax validation
python -m py_compile main.py fleet_agent.py

# Integration tests (server must be running)
$env:FLEET_TOKEN="test_token"
python tests/test_fleet_persistence.py
python tests/test_fleet_expiration.py
```

## Key Files & Conventions

### Template Structure (`templates/`)
- `fleet.html` - Main dashboard (professional dark theme, Space Grotesk font)
- Uses `fetch('/api/fleet/public')` for anonymous access (no Bearer required)
- JavaScript refreshes every 5s, includes skeleton loaders, filter/sort
- CSS: 12+ semantic classes (`.metric-card`, `.health-badge`, `.machine-grid`)

### API Endpoints
- `/api/fleet/report` (POST) - Agent uploads (rate limited 30/min, requires Bearer)
- `/api/fleet` (GET) - Authenticated fleet view (org-scoped)
- `/api/fleet/public` (GET) - Anonymous fleet view (returns ALL orgs data - security note)
- `/api/status` - Local server health metrics
- `/api/action` - Remote actions (protected by `ACTION_TOKEN` env var)

### Rate Limiting
Configured in `main.py` using `flask_limiter`:
- Default: 100/min
- `/api/fleet/report`: 30/min (high-frequency agent uploads)
- `/api/action`: 10/min (sensitive operations)

### Environment Variables
Required:
- `SECRET_KEY` - Flask session key (use `openssl rand -hex 32`)

Optional:
- `FLEET_TOKEN` - Legacy auth (deprecated, use api_keys)
- `ACTION_TOKEN` - Protects `/api/action` endpoint
- `WEBHOOK_URL` - Critical health alerts
- `FLEET_TTL_SECONDS` - Machine expiry (default 600)
- `ALLOW_DEV_INSECURE=1` - Skip SECRET_KEY for local dev

## Common Tasks

### Create New Organization
```bash
ssh root@83.150.218.175
cd /opt/dashfleet
python3 scripts/create_org.sh "Acme Corp"
# Returns: org_id and api_key
```

### Deploy Agent to Windows
```powershell
.\deploy\install_windows_complete.ps1 -ApiKey "api_xxx" -MachineId "server-01"
# Creates scheduled task running as SYSTEM
# Installs to C:\Program Files\DashFleet
```

### Deploy Agent to Linux
```bash
sudo API_KEY="api_xxx" bash deploy/install_linux_complete.sh
# Creates systemd service: dashfleet-agent
# Installs to /opt/dashfleet-agent
```

## Schema Notes (SQLite)

```sql
-- Organizations (multi-tenant root)
organizations(id TEXT PRIMARY KEY, name TEXT, created_at REAL)

-- API Keys (Bearer tokens)
api_keys(key TEXT PRIMARY KEY, org_id TEXT, created_at REAL, revoked INTEGER)

-- Fleet Data (machine metrics)
fleet(id TEXT PRIMARY KEY, report TEXT, ts REAL, client TEXT, org_id TEXT)
-- 'id' format: "org_id:machine_id"
-- 'report' is JSON blob

-- Sessions (admin login)
sessions(sid TEXT PRIMARY KEY, data TEXT, expiry REAL)
```

## Error Handling Patterns

### Marshmallow Validation
```python
# In main.py - all POST endpoints
try:
    data = schema.load(request.get_json(force=True))
except ValidationError as ve:
    logging.error(f"Validation error: {ve.messages}")
    return jsonify({"error": ve.messages}), 400
```

### TTL Expiration Logic
```python
# Machines expire after FLEET_TTL_SECONDS
now_ts = time.time()
expired = [m for m in machines if now_ts - m['ts'] > FLEET_TTL_SECONDS]
# UI shows "expired" badge, dims display
```

## Git Workflow
- Main branch: `fix/pyproject-exclude` (current production)
- Deploy: `git push origin fix/pyproject-exclude` → VPS `git pull` → `systemctl restart`
- No CI/CD pipeline (manual deployment)

## Security Considerations
- `/api/fleet/public` exposes ALL organizations' data (documented limitation)
- Store `SECRET_KEY` and `ACTION_TOKEN` in systemd environment files
- API keys stored plaintext in SQLite (rotate regularly)
- Agent config.json contains sensitive tokens (chmod 600 on Linux)

## Performance Notes
- `FLEET_STATE` in-memory dict shadows DB for fast reads
- Purges expired entries on each `/api/fleet` call
- No pagination on fleet endpoints (acceptable for <1000 machines)
- psutil metrics collection in agents takes ~0.3s CPU sampling

## Agent System Tray Icon (Windows) - NEW Jan 2026

### Feature Overview
Fleet Agent now supports a Windows system tray icon that displays:
- **Real-time metrics** (CPU, RAM, Disk %) in tooltip
- **Health status** (OK/WARN/CRITICAL) with color-coded icon
- **Pause/Resume** controls for metric collection (via right-click menu)
- **Logs viewer** - Quick access to agent log file
- **Graceful shutdown** via menu

### Implementation Details

**File Structure**:
- `fleet_agent.py` - Main agent (CLI entry point, metric collection loop)
- `fleet_agent_windows_tray.py` - Tray icon UI logic (TrayAgent class + run_tray_icon function)
- Requirements: `pystray>=0.19`, `pillow>=9.0` (PIL for icon drawing)

**Usage**:
```powershell
# Run agent with tray icon visible
python fleet_agent.py --server http://dashfleet.local --token api_xxx --tray

# Or via config.json
# (tray can be triggered via command-line flag)
```

**Architecture**:
```python
# Main agent loop checks pause state from TrayAgent
if tray_manager and tray_manager.is_paused():
    log_line(f"Agent PAUSED (via tray menu)")
    time.sleep(1)
    continue

# Tray runs in background thread (daemon)
# Updates icon/menu every 5 seconds from agent stats
# Thread-safe state via threading.Lock()
```

**Menu Items**:
- 🖥️ **Machine ID** (display only, shows hostname)
- ⏸️/**▶️ Pause/Resume Agent** (toggle pause state)
- 📋 **View Logs** (opens log file in default editor)
- ❌ **Quit** (graceful shutdown)

**Icon Design**:
- 64×64 px PIL Image
- Status colors: Green (OK), Yellow (WARN), Red (CRITICAL), Gray (PAUSED)
- Pause indicator: Red bars overlay when paused

**Compiled Executable**:
- `dist/fleet_agent.exe` (19.7 MB, built with PyInstaller)
- Single-file executable with all dependencies bundled (pystray, PIL, psutil, requests)
- Windows Task Scheduler integration ready for auto-launch at startup

### Testing
```powershell
# Syntax check
python -m py_compile fleet_agent.py fleet_agent_windows_tray.py

# Run with tray (Windows only)
python fleet_agent.py --server http://localhost:5000 --token test_token --machine-id test-pc --tray

# Verify icon appears in system tray (bottom-right corner on Windows)
# Right-click icon to access menu
# Click "Pause" to test pause state (agent stops reporting metrics)
# Click "Resume" to restart metrics collection
```

### Known Limitations
- Windows only (tray requires `pystray` which is Windows-specific; cross-platform coming later)
- Pause state is not persisted (resets on agent restart)
- Logs viewer depends on system default text editor (Notepad on Windows)

---

**Last Updated**: 2026-01-02 (Tray icon feature + tests auto-execution + status management complete)
