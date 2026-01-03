export function HelpPage() {
  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Help</div>
          <h1 style={{ margin: '6px 0' }}>Agent Deployment & Integration</h1>
          <p className="muted">Quick reference for deploying agents and using the API.</p>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        <div className="card">
          <h3>1. Deploy Agent</h3>
          <ol>
            <li>Download or build the agent (dist/fleet_agent.exe)</li>
            <li>Run: <code>fleet_agent.exe --server http://localhost:5000</code></li>
            <li>Machine ID defaults to hostname (visible in Fleet tab)</li>
            <li>Agent reports to /api/fleet/report every 30 seconds</li>
          </ol>
        </div>

        <div className="card">
          <h3>2. Main Endpoints</h3>
          <ul>
            <li><strong>GET /api/stats</strong> - Current system stats</li>
            <li><strong>GET /api/status</strong> - Stats + health score</li>
            <li><strong>GET /api/fleet</strong> - All fleet machines</li>
            <li><strong>GET /api/history?limit=300</strong> - CSV history data</li>
            <li><strong>POST /api/fleet/report</strong> - Agent reports metrics</li>
            <li><strong>POST /api/action</strong> - Run system actions</li>
          </ul>
        </div>

        <div className="card">
          <h3>3. No Authentication</h3>
          <p>This simplified version has no login, API keys, or organizations.</p>
          <p>All endpoints are public. Use in trusted networks only.</p>
        </div>

        <div className="card">
          <h3>4. System Actions</h3>
          <p>Windows-only maintenance tasks:</p>
          <ul>
            <li>flush_dns - Flush DNS cache</li>
            <li>restart_spooler - Restart print spooler</li>
            <li>cleanup_temp - Clean temp files</li>
            <li>cleanup_teams - Clean Teams cache</li>
            <li>cleanup_outlook - Clean Outlook cache</li>
            <li>collect_logs - Collect diagnostic logs</li>
          </ul>
        </div>

        <div className="card">
          <h3>5. Environment Variables</h3>
          <ul>
            <li><strong>HOST</strong> - Flask host (default: 0.0.0.0)</li>
            <li><strong>PORT</strong> - Flask port (default: 5000)</li>
            <li><strong>FLEET_TTL_SECONDS</strong> - Fleet entry expiration (default: 600)</li>
            <li><strong>WEBHOOK_URL</strong> - Send alerts to webhook on critical health</li>
          </ul>
        </div>

        <div className="card">
          <h3>6. Running the Dashboard</h3>
          <ul>
            <li><strong>Web mode:</strong> <code>python main.py --web</code> (auto-opens browser)</li>
            <li><strong>CLI mode:</strong> <code>python main.py</code> (terminal output)</li>
            <li><strong>Export:</strong> <code>--export-csv ~/metrics.csv</code></li>
          </ul>
        </div>
      </div>

      <div className="card">
        <h3>Dashboard Pages</h3>
        <p><strong>Live:</strong> Real-time metrics, health score, system actions</p>
        <p><strong>Fleet:</strong> All connected machines, status, health scores</p>
        <p><strong>History:</strong> Historical charts from CSV logs</p>
        <p><strong>Help:</strong> This page</p>
      </div>

      <div className="card">
        <h3>Agent Reporting Format</h3>
        <pre style={{ fontSize: '0.85em', overflow: 'auto', maxHeight: '300px' }}>
{`POST /api/fleet/report
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
}`}
        </pre>
      </div>
    </div>
  );
}
