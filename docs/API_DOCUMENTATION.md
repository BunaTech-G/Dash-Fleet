# DashFleet API Documentation (Swagger/OpenAPI 3.0)

This file documents all DashFleet API endpoints and schemas.

## Base URL

Production: `https://dash-fleet.com`
Local: `http://localhost:5000`

## Authentication

**Bearer Token Authentication** (required for most endpoints)

```
Authorization: Bearer <api_key>
```

API keys are managed in the `api_keys` table (SQLite).

## Endpoints

### 1. POST /api/fleet/report

**Description:** Submit fleet metrics from an agent

**Authentication:** Required (Bearer token)

**Rate Limit:** 30 requests/minute per token

**Request Body:**
```json
{
  "machine_id": "string (hostname)",
  "report": {
    "cpu_percent": "float (0-100)",
    "ram_percent": "float (0-100)",
    "disk_percent": "float (0-100)",
    "uptime": "integer (seconds)",
    "timestamp": "float (unix timestamp, optional)"
  }
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "machine_id": "hostname",
  "org_id": "org-uuid"
}
```

**Response (400 Bad Request):**
```json
{
  "error": {
    "cpu_percent": ["Must be between 0 and 100"],
    "ram_percent": ["Field is required"]
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid or missing API key"
}
```

**Example Request:**
```bash
curl -X POST https://dash-fleet.com/api/fleet/report \
  -H "Authorization: Bearer api_d2f6f9a8-3c7e-4c1f-9b0f-123456789abc" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "kclient1",
    "report": {
      "cpu_percent": 35.5,
      "ram_percent": 62.1,
      "disk_percent": 45.3,
      "uptime": 86400
    }
  }'
```

---

### 2. GET /api/fleet

**Description:** Retrieve all machines in organization

**Authentication:** Required (Bearer token - org scoped)

**Query Parameters:**
- `sort_by`: `hostname`, `health`, `cpu`, `ram`, `disk` (default: `hostname`)
- `filter_status`: `ok`, `warn`, `critical` (optional)

**Response (200 OK):**
```json
{
  "machines": [
    {
      "id": "org-uuid:hostname",
      "machine_id": "hostname",
      "client": "192.168.1.100",
      "org_id": "org-uuid",
      "ts": 1704067200.0,
      "report": {
        "cpu_percent": 35.5,
        "ram_percent": 62.1,
        "disk_percent": 45.3,
        "uptime": 86400
      },
      "health": {
        "score": 78,
        "status": "ok"
      },
      "ttl_remaining_seconds": 86300,
      "expired": false
    }
  ],
  "count": 5,
  "org_id": "org-uuid"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid API key"
}
```

**Example Request:**
```bash
curl -H "Authorization: Bearer api_d2f6f9a8-3c7e-4c1f-9b0f-123456789abc" \
  https://dash-fleet.com/api/fleet?sort_by=health
```

---

### 3. GET /api/fleet/public

**Description:** Retrieve all machines across all organizations (public, no auth required)

**⚠️ Security Note:** Exposes data from ALL organizations. Do not expose in untrusted environments.

**Query Parameters:**
- Same as `/api/fleet`

**Response (200 OK):**
```json
{
  "machines": [
    {
      "id": "org-uuid:hostname",
      "machine_id": "hostname",
      "client": "192.168.1.100",
      "org_id": "org-uuid",
      "report": {
        "cpu_percent": 35.5,
        "ram_percent": 62.1,
        "disk_percent": 45.3
      },
      "health": {
        "score": 78,
        "status": "ok"
      }
    }
  ],
  "count": 12
}
```

**Example Request:**
```bash
curl https://dash-fleet.com/api/fleet/public
```

---

### 4. GET /api/status

**Description:** Get local server health metrics (no auth required)

**Response (200 OK):**
```json
{
  "status": "ok",
  "uptime": 86400,
  "machines_total": 5,
  "database": "sqlite",
  "version": "1.0.0"
}
```

**Example Request:**
```bash
curl http://localhost:5000/api/status
```

---

## Data Models

### FleetEntry

Represents a single machine in the fleet.

```json
{
  "id": "org-uuid:hostname",
  "machine_id": "string (hostname)",
  "client": "string (IP address or hostname)",
  "org_id": "string (organization UUID)",
  "ts": "float (unix timestamp when last reported)",
  "report": {
    "cpu_percent": "float (0-100)",
    "ram_percent": "float (0-100)",
    "disk_percent": "float (0-100)",
    "uptime": "integer (seconds)",
    "timestamp": "float (unix timestamp, optional)"
  },
  "health": {
    "score": "integer (0-100)",
    "status": "string (ok|warn|critical)"
  },
  "ttl_remaining_seconds": "integer (seconds until expiration)",
  "expired": "boolean"
}
```

### HealthScore

Health score calculation based on system metrics.

```json
{
  "score": "integer (0-100)",
  "status": "string (ok|warn|critical)",
  "calculation": {
    "cpu_weight": 35,
    "ram_weight": 35,
    "disk_weight": 30,
    "thresholds": {
      "ok_minimum": 80,
      "warn_minimum": 60
    }
  }
}
```

**Health Score Algorithm:**
- CPU > 50% → linear penalty to 0 at 100%
- RAM > 60% → linear penalty to 0 at 100%
- Disk > 70% → linear penalty to 0 at 100%
- Weighted: CPU 35% + RAM 35% + Disk 30%
- Status:
  - `ok`: score ≥ 80
  - `warn`: 60 ≤ score < 80
  - `critical`: score < 60

### ErrorResponse

Standard error response format.

```json
{
  "error": "string or object",
  "status": "error"
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/fleet/report` | 30 | per minute |
| `/api/fleet` | 100 | per minute |
| `/api/fleet/public` | 100 | per minute |
| `/api/status` | 100 | per minute |

Rate limit headers in response:
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - API key revoked or org mismatch |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Example Workflows

### 1. Agent Reporting Cycle

```
Agent (fleet_agent.py):
1. Read config.json (server, token, interval)
2. Collect metrics (psutil)
3. Every N seconds:
   a. POST /api/fleet/report with metrics
   b. Wait for 200 OK response
   c. Log success/failure
   d. Sleep until next interval
```

### 2. Dashboard Refresh Cycle

```
Browser (fleet.html):
1. Every 5 seconds:
   a. GET /api/fleet/public or /api/fleet (with Bearer token)
   b. Receive machines list with health scores
   c. Update UI (differential rendering - no flicker)
   d. Calculate TTL countdown
   e. Show "expired" badge if TTL exceeded
```

### 3. Organization Management

```
Admin:
1. Create organization via DB or create_org.sh
2. Generate API key → stores in api_keys table
3. Share token with agent admins
4. Agents use token for all /api/fleet/report calls
5. Organization data isolated by org_id foreign key
```

---

## Authentication Flow

```
1. Agent/Client has API key (from api_keys table)
   Example: api_d2f6f9a8-3c7e-4c1f-9b0f-123456789abc

2. Send request with Bearer token:
   Authorization: Bearer api_d2f6f9a8-3c7e-4c1f-9b0f-123456789abc

3. Server checks _check_org_key():
   a. Extract token from Authorization header
   b. Query api_keys table WHERE key = token AND revoked = 0
   c. Get org_id from matching row
   d. Filter all queries by org_id

4. Response scoped to organization:
   - /api/fleet only returns machines for that org
   - /api/fleet/report saves with that org_id
```

---

## Environment Variables

**Required:**
- `SECRET_KEY`: Flask session key (use `openssl rand -hex 32`)

**Optional:**
- `FLEET_TTL_SECONDS`: Machine expiry timeout (default: 86400 = 24 hours)
- `ACTION_TOKEN`: API key for `/api/action` endpoint
- `WEBHOOK_URL`: Send alerts on critical health
- `ALLOW_DEV_INSECURE`: Skip SECRET_KEY check (dev only)

---

## Database Schema

```sql
CREATE TABLE organizations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at REAL NOT NULL
);

CREATE TABLE api_keys (
  key TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  created_at REAL NOT NULL,
  revoked INTEGER DEFAULT 0,
  FOREIGN KEY (org_id) REFERENCES organizations(id)
);

CREATE TABLE fleet (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  report TEXT NOT NULL,
  ts REAL NOT NULL,
  client TEXT,
  FOREIGN KEY (org_id) REFERENCES organizations(id)
);

CREATE TABLE sessions (
  sid TEXT PRIMARY KEY,
  data TEXT NOT NULL,
  expiry REAL NOT NULL
);
```

---

## CORS & Security

**CORS Enabled For:**
- `GET /api/fleet/public`
- `GET /api/fleet` (with Bearer token)

**HTTPS Required For:**
- All endpoints in production (83.150.218.175)
- Redirect HTTP → HTTPS via Nginx

**Content Security Policy:**
- Inline scripts allowed for dashboard (fleet.html)
- No external resource loading

---

## Deployment Notes

**Gunicorn Configuration (Production):**
```
workers: 3
worker_class: sync
timeout: 30
bind: 127.0.0.1:5000
```

**Nginx Reverse Proxy:**
- Listens on port 443 (HTTPS)
- Proxies to Gunicorn (127.0.0.1:5000)
- Let's Encrypt SSL certificate
- GZIP compression enabled

---

## Monitoring & Logging

**Log Files:**
- API: `/var/log/dashfleet/api.log`
- Agent: `logs/agent.log` (local)
- Fleet state: `logs/fleet_state.json` (in-memory cache dump)

**Metrics CSV:**
- Path: `logs/metrics.csv`
- Tracks: timestamp, machine_id, cpu%, ram%, disk%

**Systemd Service:**
```
systemctl status dashfleet
systemctl restart dashfleet
journalctl -u dashfleet -f
```

---

**Last Updated:** 2026-01-02
**API Version:** 1.0.0
**OpenAPI Version:** 3.0.0
