# Fleet Agent Tray Icon Setup Guide

## Overview

The Fleet Agent now includes an optional **Windows system tray icon** that provides real-time metrics display, pause/resume controls, and quick log access directly from your system tray.

## Features

- **Real-time Metrics Display**: CPU, RAM, and Disk usage in tooltip
- **Health Status Indicator**: Color-coded icon (Green=OK, Yellow=Warning, Red=Critical, Gray=Paused)
- **Pause/Resume Controls**: Right-click menu to pause/resume metric collection
- **Quick Logs Access**: Open agent log file from menu
- **Graceful Shutdown**: Quit from menu

## Requirements

### System
- **Windows 7 or later** (uses pystray which is Windows-specific)
- Python 3.7+

### Dependencies
```
pystray>=0.19
pillow>=9.0
psutil>=5.8
requests>=2.0
```

These are included in `requirements.txt` and bundled in `dist/fleet_agent.exe`.

## Running with Tray Icon

### Option 1: Python Script (Development)
```powershell
# From project directory
python fleet_agent.py --server http://localhost:5000 --token api_xxx --tray

# Or with config file
python fleet_agent.py --config config.json --tray
```

### Option 2: Compiled Executable (Production)
```powershell
# Use the pre-compiled exe
C:\Program Files\DashFleet\fleet_agent.exe --server http://dashfleet.local --token api_xxx --tray

# Or with Windows Task Scheduler for auto-start
```

### Option 3: Config File
Create `config.json`:
```json
{
  "server": "https://dash-fleet.example.com",
  "path": "/api/fleet/report",
  "token": "api_xxx",
  "interval": 30,
  "machine_id": "office-pc-001",
  "log_file": "logs/agent.log"
}
```

Then run:
```powershell
python fleet_agent.py --config config.json --tray
```

## Menu Options

### Machine ID (Display Only)
Shows the hostname or custom machine ID configured for this agent.

### Pause / Resume Agent
- **Pause**: Temporarily stops metric collection and reporting (shows "PAUSED" in status tooltip)
- **Resume**: Restarts metric collection
- **Note**: Pause state is NOT persisted; agent resumes on restart

### View Logs
Opens the agent log file in your system default text editor (usually Notepad on Windows).

**Requirements:**
- Log file path must be configured (use `--log-file` or config.json)
- Text editor must be set as default for `.log` files

### Quit
Gracefully shuts down the agent process and removes the tray icon.

## Tray Icon Status

### Color Meanings
- 🟢 **Green**: Health score ≥ 80 (OK)
- 🟡 **Yellow**: Health score 60-79 (Warning)
- 🔴 **Red**: Health score < 60 (Critical)
- ⚫ **Gray**: Agent is PAUSED

### Tooltip Display
Hover over the tray icon to see:
```
DashFleet Agent
━━━━━━━━━━━━━━
Status: ONLINE (or PAUSED)
Health Score: 85/100
━━━━━━━━━━━━━━
CPU: 35.2%
RAM: 62.1%
Disk: 48.9%
```

Updates every 5 seconds.

## Troubleshooting

### Tray Icon Not Appearing
1. Check system tray area (bottom-right of taskbar)
2. Click the up arrow to show hidden icons
3. Verify agent started with `--tray` flag
4. Check log file for errors: `⏸️` (Pause) → View Logs

### "pystray/pillow not installed" Error
Install dependencies:
```powershell
pip install pystray>=0.19 pillow>=9.0
```

Or use the pre-compiled exe which has all dependencies bundled.

### View Logs Not Working
1. Ensure `--log-file` or `log_file` in config is set
2. Verify log file path exists and is readable
3. Set a text editor as default for `.log` files (Windows File Explorer → right-click .log → "Open with" → select editor)

### Agent Still Running When Quit from Menu
1. Check Windows Task Manager (Ctrl+Shift+Esc) for `python.exe` or `fleet_agent.exe` process
2. Right-click process and "End Task"

## Windows Task Scheduler Integration

### Schedule with Tray Icon (Windows 10/11)

**Option A: Using PowerShell Script**
```powershell
# Create scheduled task
$taskName = "DashFleet Agent"
$action = New-ScheduledTaskAction `
  -Execute "C:\Program Files\DashFleet\fleet_agent.exe" `
  -Argument "--server https://dashfleet.local --token api_xxx --tray"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId SYSTEM -LogonType ServiceAccount
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal
```

**Option B: Manual Task Scheduler**
1. Open Windows Task Scheduler (taskschd.msc)
2. Click "Create Task..."
3. Set:
   - **Name**: DashFleet Agent
   - **Trigger**: At Startup
   - **Action**: Start a program
     - **Program**: `C:\Program Files\DashFleet\fleet_agent.exe`
     - **Arguments**: `--server https://dashfleet.local --token api_xxx --tray`
4. Click OK

## Performance Notes

- Tray icon updates every 5 seconds (minimal overhead)
- Pause state only affects metric collection, not log storage
- Metric collection continues in background thread while tray menu is open

## Limitations

- **Windows Only**: Tray icon requires Windows (uses pystray); cross-platform support coming later
- **Pause Not Persisted**: Pause state resets when agent restarts
- **Log Viewer Dependency**: Uses system default text editor for logs

## Examples

### Development Setup
```powershell
# Terminal 1: Start server
python main.py --web --host localhost --port 5000

# Terminal 2: Start agent with tray icon
python fleet_agent.py --server http://localhost:5000 --token dev_token --machine-id my-pc --tray --log-file logs/agent.log
```

### Production Deployment
```powershell
# Copy exe to Program Files
Copy-Item -Path .\dist\fleet_agent.exe -Destination "C:\Program Files\DashFleet\"

# Create config
@'
{
  "server": "https://dashfleet.example.com",
  "token": "api_prod_key_xxx",
  "machine_id": "prod-server-01",
  "interval": 60,
  "log_file": "C:\Program Files\DashFleet\logs\agent.log"
}
'@ | Out-File -Encoding utf8 "C:\Program Files\DashFleet\config.json"

# Register scheduled task (see section above)
```

---

For more information, see:
- [README.md](../readme.md) - General DashFleet documentation
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Technical architecture
- [RELEASE_NOTES.md](../RELEASE_NOTES.md) - Version history
