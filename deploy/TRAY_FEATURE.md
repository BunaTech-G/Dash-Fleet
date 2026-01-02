# Fleet Agent Windows Tray Feature

## Overview
The Fleet Agent now supports a Windows system tray icon that displays real-time metrics and health status.

## Features
- **System Tray Icon**: Minimizes to taskbar with colored status indicator
- **Real-time Metrics**: CPU, RAM, Disk usage in tooltip
- **Health Score**: Visual status badge (green=ok, yellow=warn, red=critical)
- **Quick Access**: Right-click menu to quit
- **Background Monitoring**: Non-blocking tray display

## Installation

### Option 1: Using Pre-Built Executable
1. Download `fleet_agent.exe` from `/deploy/agent_binaries/`
2. Place it in your deployment directory
3. Run with: `fleet_agent.exe --server https://dash-fleet.com --token api_xxx --tray`

### Option 2: Building from Source
Prerequisites:
```powershell
pip install pystray pillow psutil requests
```

Build the executable:
```powershell
cd C:\path\to\DASH-FLEET
pyinstaller fleet_agent.spec
```

The compiled executable will be in `dist\fleet_agent.exe`

## Usage

### Basic Tray Mode
```powershell
.\fleet_agent.exe --server https://dash-fleet.com --token api_xxx --tray
```

### With Configuration File
```powershell
.\fleet_agent.exe --config config.json --tray
```

### Command-Line Options
```
--server SERVER          Server URL (without path)
--path PATH             Endpoint path (default: /api/fleet/report)
--token TOKEN           API token for authentication
--interval INTERVAL     Reporting interval in seconds (default: 30)
--machine-id MACHINE_ID Custom machine identifier
--tray                  Enable Windows system tray icon
--log-file LOG_FILE     Local log file path (optional)
```

## Configuration File Format (config.json)
```json
{
  "server": "https://dash-fleet.com",
  "path": "/api/fleet/report",
  "token": "api_xxx",
  "interval": 30,
  "machine_id": "server-01",
  "log_file": "logs/agent.log"
}
```

## Icon Status Indicators

| Status | Color  | Meaning |
|--------|--------|---------|
| ✓ OK | Green | All metrics healthy (score ≥ 80) |
| ⚠ WARN | Yellow | Moderate resource usage (score 60-79) |
| ✗ CRITICAL | Red | High resource usage (score < 60) |
| ⚪ OFFLINE | Gray | No connection or error state |

## Tooltip Information
Hover over the tray icon to see:
- Current health status
- Health score (0-100)
- CPU usage percentage
- RAM usage percentage
- Disk usage percentage

## Requirements

### Windows
- Windows 7 or later
- For Python version:
  - Python 3.8+
  - `pip install pystray pillow psutil requests`

### External Dependencies
- **pystray**: System tray icon support
- **Pillow (PIL)**: Icon image generation
- **psutil**: System metrics collection
- **requests**: HTTP client for server communication

## Deployment via PowerShell Script

A deployment script is provided for automated Windows agent installation:

```powershell
# Download and run installation script
$ApiKey = "api_xxx"
$MachineId = "server-01"
.\deploy\install_agent_windows.ps1 -ApiKey $ApiKey -MachineId $MachineId
```

This script:
1. Downloads fleet_agent.exe
2. Creates `C:\Program Files\DashFleet\` directory
3. Sets up a scheduled task for auto-start
4. Configures tray icon mode for background monitoring

## Troubleshooting

### Missing Modules Error
If you see: `[TRAY] ⚠️ pystray/pillow not installés...`

**Solution**: Install missing packages:
```powershell
pip install pystray pillow
```

### Tray Icon Not Appearing
1. Check Windows display settings (some systems hide tray by default)
2. Verify pystray is installed: `pip show pystray`
3. Try running without `--tray` to test metrics collection:
   ```powershell
   .\fleet_agent.exe --server https://dash-fleet.com --token api_xxx
   ```

### High CPU Usage
If the agent uses excessive CPU:
1. Increase `--interval` value (e.g., 60 seconds instead of 30)
2. Disable tray icon mode if not needed

### Connection Issues
```powershell
# Test connectivity
$ApiKey = "api_xxx"
curl -H "Authorization: Bearer $ApiKey" https://dash-fleet.com/api/fleet
```

## Development

### Source Files
- `fleet_agent.py` - Main agent logic
- `fleet_agent_windows_tray.py` - Tray icon implementation
- `fleet_utils.py` - Shared utilities
- `fleet_agent.spec` - PyInstaller configuration

### Building from Source
```powershell
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --clean fleet_agent.spec

# Result: dist/fleet_agent.exe
```

### Customizing Icon
To modify the icon image:
1. Edit `create_image()` function in `fleet_agent_windows_tray.py`
2. Rebuild with `pyinstaller fleet_agent.spec`

## Performance Notes
- Tray icon updates every 5 seconds
- Metrics collection takes ~0.3s CPU sampling
- Typical memory usage: 40-80 MB
- Network: 1 POST request every 30 seconds (default interval)

## Support
For issues or feature requests, contact the DashFleet team.

---
Last Updated: 2026-01-02
