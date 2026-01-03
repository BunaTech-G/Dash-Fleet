# DashFleet Agent - Professional Windows Installation Guide

## 🚀 Quick Start (Recommended)

### Option 1: One-Click Installer (Easiest)

1. Download `Install-DashFleetAgent.bat`
2. **Right-click** and select **"Run as administrator"**
3. Wait for the installation to complete
4. The agent will automatically start on next Windows boot

That's it! The agent will now:
- ✅ Run in the background with system tray icon
- ✅ Auto-start every time Windows boots
- ✅ Report metrics to your DashFleet server every 30 seconds
- ✅ Show status in system tray (bottom-right corner)

### Option 2: PowerShell Installation

Open PowerShell as Administrator and run:

```powershell
# Download and execute the installer
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
Invoke-WebRequest -Uri "https://github.com/BunaTech-G/Dash-Fleet/raw/feat/react-spa/Install-DashFleetAgent.ps1" -OutFile "$env:TEMP\Install-DashFleetAgent.ps1"
& "$env:TEMP\Install-DashFleetAgent.ps1" -ServerUrl "https://dash-fleet.com"
```

### Option 3: Manual Installation

If you prefer manual installation:

```powershell
# 1. Install Python (if not already installed)
# Download from https://www.python.org/downloads/

# 2. Install dependencies
pip install psutil pystray pillow

# 3. Run the agent
python fleet_agent_pro.py --server https://dash-fleet.com
```

---

## 📋 System Requirements

- **Windows 10/11** (or Windows Server 2016+)
- **Python 3.10 or later** (optional if using installer)
- **.NET Framework 4.5+** (usually already installed)
- **Internet connection** to report metrics

---

## 🎯 What the Installer Does

1. **Checks Python Installation**
   - Verifies Python is installed and accessible
   - If missing, shows download instructions

2. **Creates Installation Directory**
   - Installs files to `C:\Program Files\DashFleet`

3. **Downloads Agent**
   - Downloads latest agent from GitHub
   - Verifies integrity

4. **Installs Dependencies**
   - Automatically installs: `psutil`, `pillow`, `pystray`
   - No manual pip commands needed

5. **Creates Shortcuts**
   - Adds "DashFleet Agent" to Windows Start Menu
   - Easy access to agent launcher and settings

6. **Enables Auto-Start**
   - Configures Windows Registry for automatic startup
   - Agent will run on every boot (no user login needed)

7. **Tests Installation**
   - Runs agent briefly to verify everything works
   - Shows any errors immediately

---

## 📊 System Tray Icon

Once installed, you'll see a **dashboard icon** in your Windows system tray (bottom-right corner):

### Icon Status
- 🟢 **Green** = Agent healthy (all metrics OK)
- 🟡 **Yellow** = Warning (some metrics above threshold)
- 🔴 **Red** = Critical (metrics critically high)

### Right-Click Menu
- **Status**: Shows current agent status
- **Exit**: Stops the agent

---

## 📝 Log Files

Agent logs are saved to:
```
C:\Users\[YourUsername]\dashfleet_agent.log
```

View logs to troubleshoot issues:
```powershell
Get-Content "$env:USERPROFILE\dashfleet_agent.log" -Tail 50
```

---

## ⚙️ Configuration

### Change Server URL
Edit the batch file: `C:\Program Files\DashFleet\start-agent.bat`

Change this line:
```batch
python "%~dp0agent.py" --server YOUR_SERVER_URL --machine-id MACHINE_NAME
```

### Disable Auto-Start
Go to: **Settings > Apps > Startup**
Find "DashFleet Agent" and toggle OFF

Or run in PowerShell:
```powershell
python "C:\Program Files\DashFleet\agent.py" --disable-autostart
```

### Change Report Interval
Edit `start-agent.bat` and add `--interval 60` for 60-second intervals:
```batch
python "%~dp0agent.py" --server https://dash-fleet.com --interval 60
```

---

## 🔧 Command-Line Options

```
Usage: python fleet_agent_pro.py [options]

Options:
  --server URL           DashFleet server URL
                        (default: http://localhost:5000)
  --machine-id ID       Custom machine ID
                        (default: computer hostname)
  --interval SECONDS    Report interval in seconds
                        (default: 30)
  --no-tray            Disable system tray icon
  --disable-autostart  Disable Windows auto-start
  -h, --help           Show this help message
```

### Examples:
```powershell
# Custom server and interval
python agent.py --server https://my-server.com --interval 60

# Without tray icon
python agent.py --no-tray

# Disable auto-start
python agent.py --disable-autostart
```

---

## 🗑️ Uninstall

### Method 1: Using Installer Script
```powershell
powershell -ExecutionPolicy Bypass -File "C:\path\to\Install-DashFleetAgent.ps1" -Uninstall
```

### Method 2: Manual Uninstall
1. Stop the agent from system tray
2. Delete `C:\Program Files\DashFleet` folder
3. Remove from startup (Settings > Apps > Startup)
4. Delete Start Menu shortcuts

---

## 🐛 Troubleshooting

### Agent won't start
1. Check Python is installed: `python --version`
2. Check dependencies: `pip list | grep psutil`
3. Try manual run: `python "C:\Program Files\DashFleet\agent.py"`
4. Check logs: `C:\Users\[You]\dashfleet_agent.log`

### Can't see system tray icon
1. Make sure agent is running
2. Check Windows tray settings (Icon might be hidden)
3. Click the "^" arrow in system tray to show hidden icons
4. Try reinstalling with `Install-DashFleetAgent.bat`

### "Python not found" error
1. Install Python from https://www.python.org
2. Make sure to check "Add Python to PATH" during installation
3. Restart installer after Python installation

### Failed to report to server
1. Check server URL: `ping dash-fleet.com`
2. Check internet connection
3. Check firewall doesn't block HTTPS traffic
4. Check logs for error details

### High CPU/RAM usage
1. Increase report interval: `--interval 120` (report every 2 minutes)
2. Disable tray icon if not needed: `--no-tray`
3. Check for Windows processes using CPU: `tasklist /v`

---

## 📚 Additional Resources

- **GitHub**: https://github.com/BunaTech-G/Dash-Fleet
- **Server Dashboard**: https://dash-fleet.com
- **Documentation**: See server help page

---

## 🆘 Support

If you encounter issues:

1. **Check the logs**: `$env:USERPROFILE\dashfleet_agent.log`
2. **Run manually** to see error messages:
   ```powershell
   python "C:\Program Files\DashFleet\agent.py" --server https://dash-fleet.com
   ```
3. **Report on GitHub**: https://github.com/BunaTech-G/Dash-Fleet/issues

---

## 📄 License

DashFleet Agent is part of the DashFleet project.

---

**Version**: 1.0.0
**Last Updated**: January 3, 2026
**Status**: Professional Release ✓
