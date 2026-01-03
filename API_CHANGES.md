# API Endpoints Documentation

## Changes from Old to New

### ❌ REMOVED (Authentication & Multi-tenant)
```
POST /api/login              - Exchange API key for session (REMOVED)
POST /api/logout             - Clear session (REMOVED)
POST /api/orgs               - Create organization (REMOVED)
GET  /api/orgs               - List organizations (REMOVED)
POST /api/keys/revoke        - Revoke API key (REMOVED)
POST /api/tokens/*           - Token management (REMOVED)
GET  /download/agent/<token> - Agent download (REMOVED)
```

### ✅ SIMPLIFIED (No Authentication Required)

#### `GET /api/stats`
Returns current system statistics without health score.
```json
{
  "timestamp": "2025-01-03T14:30:45.123456",
  "hostname": "DESKTOP-ABC123",
  "cpu_percent": 45.2,
  "ram_percent": 62.5,
  "ram_used_gib": 8.5,
  "ram_total_gib": 16.0,
  "disk_percent": 72.1,
  "disk_used_gib": 360.0,
  "disk_total_gib": 500.0,
  "uptime_seconds": 864000,
  "uptime_hms": "240:00:00",
  "alerts": { "cpu": false, "ram": false },
  "alert_active": false
}
```

#### `GET /api/status`
Returns stats WITH health score.
```json
{
  ...stats...
  "health": {
    "score": 78,
    "status": "ok",
    "components": { "cpu": 90, "ram": 75, "disk": 65 }
  }
}
```

#### `GET /api/fleet`
Returns all machines currently reporting.
```json
{
  "count": 3,
  "data": [
    {
      "id": "machine-1",
      "hostname": "DESKTOP-ABC123",
      "ts": 1704283845.123,
      "client": "192.168.1.100",
      "report": { ...stats... }
    },
    ...
  ]
}
```

#### `GET /api/history?limit=300`
Returns historical data from CSV logs.
```json
{
  "count": 150,
  "data": [
    {
      "timestamp": "2025-01-03T14:30:45",
      "hostname": "DESKTOP-ABC123",
      "cpu_percent": 45.2,
      "ram_percent": 62.5,
      "disk_percent": 72.1,
      "uptime_hms": "240:00:00"
    },
    ...
  ]
}
```

#### `POST /api/fleet/report`
Agent reports its metrics. No authentication required.
```json
{
  "machine_id": "DESKTOP-ABC123",
  "hostname": "DESKTOP-ABC123",
  "report": {
    "timestamp": "2025-01-03T14:30:45.123456",
    "hostname": "DESKTOP-ABC123",
    "cpu_percent": 45.2,
    "ram_percent": 62.5,
    "ram_used_gib": 8.5,
    "ram_total_gib": 16.0,
    "disk_percent": 72.1,
    "disk_used_gib": 360.0,
    "disk_total_gib": 500.0,
    "uptime_seconds": 864000,
    "uptime_hms": "240:00:00",
    "alerts": { "cpu": false, "ram": false },
    "alert_active": false,
    "health": {
      "score": 78,
      "status": "ok",
      "components": { "cpu": 90, "ram": 75, "disk": 65 }
    }
  }
}
```

Response:
```json
{ "ok": true }
```

#### `POST /api/action`
Run approved system actions (Windows only).
```json
{
  "action": "flush_dns"
}
```

Available actions:
- `flush_dns` - Flush DNS cache
- `restart_spooler` - Restart print spooler
- `cleanup_temp` - Clean temp files
- `cleanup_teams` - Clean Teams cache
- `cleanup_outlook` - Clean Outlook cache
- `collect_logs` - Collect diagnostic logs

Response:
```json
{
  "action": "flush_dns",
  "ok": true,
  "stdout": "Successfully flushed the DNS Resolver Cache",
  "code": 0
}
```

## Frontend API Client

### New Simplified Functions

```typescript
// Get current stats
fetchStats(): Promise<SystemStats>

// Get stats with health score
fetchStatus(): Promise<SystemStats>

// Get fleet machines
fetchFleet(): Promise<FleetEntry[]>

// Get history
fetchHistory(limit = 300): Promise<HistoryRow[]>

// Run action
runAction(action: string): Promise<any>
```

### No more:
- `buildHeaders(apiKey)` - No API key support
- `fetchTokens()`
- `createToken()`
- `deleteToken()`
- Auth-related functions

## Frontend React Hooks

```typescript
// Fleet hook
const { data, isLoading, error } = useFleet()

// Stats hook
const { data, isFetching, error } = useStats()

// History hook
const { data, isLoading, error } = useHistory(limit)
```

## Environment Variables

### Backend
- `HOST` (default: 0.0.0.0) - Flask host
- `PORT` (default: 5000) - Flask port
- `FLEET_TTL_SECONDS` (default: 600) - Fleet entry expiration
- `WEBHOOK_URL` (optional) - Webhook for critical alerts
- `WEBHOOK_MIN_SECONDS` (default: 300) - Min time between webhook alerts

### Frontend
- `VITE_FLEET_TTL` (default: 600) - Display TTL in UI

## Key Differences

| Feature | Old | New |
|---------|-----|-----|
| Authentication | API Keys + Sessions | None |
| Organizations | Multi-tenant | Single instance |
| /api/login | Yes | Removed |
| /api/fleet requires auth | Yes | No |
| /api/history requires auth | Yes | No |
| Agent reporting | Requires FLEET_TOKEN | No token needed |
| Hostname | Optional | Automatic (socket.gethostname) |
| Health score | Calculated per-machine | Calculated + included in report |

## Usage Examples

### Get current stats
```bash
curl http://localhost:5000/api/stats
```

### Get all fleet machines
```bash
curl http://localhost:5000/api/fleet
```

### Agent report (no auth)
```bash
curl -X POST http://localhost:5000/api/fleet/report \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "my-machine",
    "hostname": "DESKTOP-XYZ",
    "report": { ...stats object... }
  }'
```

### Run cleanup action
```bash
curl -X POST http://localhost:5000/api/action \
  -H "Content-Type: application/json" \
  -d '{ "action": "cleanup_temp" }'
```
