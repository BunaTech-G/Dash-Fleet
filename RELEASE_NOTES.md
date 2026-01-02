# DashFleet Release Notes

## Version 2.0.0 - 2026-01-02

### 🎉 NEW FEATURES

#### Windows System Tray Icon for Fleet Agent
- **Visual System Tray Icon**: Real-time display of agent metrics (CPU, RAM, Disk %) in Windows system tray tooltip
- **Health Status Indicator**: Color-coded icon showing agent health status (Green/Yellow/Red/Gray)
- **Pause/Resume Control**: Right-click menu to pause metric collection (useful for maintenance or reducing system load)
- **Quick Logs Access**: View agent logs directly from tray menu
- **Graceful Shutdown**: Quit application from tray menu

**Usage:**
```powershell
python fleet_agent.py --server http://dashfleet.local --token api_xxx --tray
```

**Requirements:**
- Windows OS (uses `pystray` which is Windows-specific)
- `pystray>=0.19` and `pillow>=9.0` (now in requirements.txt)

**Implementation:**
- `fleet_agent_windows_tray.py` - Tray UI module with `TrayAgent` class and `run_tray_icon()` function
- `fleet_agent.py` - Updated with tray initialization and pause state handling in main loop
- Thread-safe pause state with `threading.Lock()`
- Background thread runs tray icon without blocking metric collection

**Compiled Executable:**
- `dist/fleet_agent.exe` (19.7 MB) - Ready for Windows Task Scheduler deployment

### ✅ TESTING
- Added `tests/test_tray_icon.py` - Tests for TrayAgent initialization, pause/resume, icon creation
- Added `tests/test_agent_integration.py` - Integration tests for agent help output and syntax validation
- **All 6 tests passing** ✓

### 📝 DOCUMENTATION
- Updated `.github/copilot-instructions.md` with complete tray icon feature documentation
- Known limitations documented: Windows-only, pause state not persisted, log viewer depends on system editor

### 🔧 TECHNICAL DETAILS

**Architecture:**
```python
# Tray runs in background thread (daemon)
tray_thread = threading.Thread(
    target=lambda: run_tray_icon(...),
    daemon=True
)
tray_thread.start()

# Main agent loop checks pause state
if tray_manager and tray_manager.is_paused():
    log_line("Agent PAUSED")
    time.sleep(1)
    continue
```

**Menu Structure:**
- 🖥️ Machine ID (read-only display)
- ⏸️ / ▶️ Pause/Resume Agent (toggle)
- 📋 View Logs (opens in default editor)
- ❌ Quit (graceful shutdown with sys.exit())

**Icon Design:**
- 64×64 pixel PIL Image
- Status colors: #22C55E (OK), #FACC15 (WARN), #F43F5E (CRITICAL), #9CA3AF (PAUSED)
- Pause indicator: Red bars overlay when paused

### 🐛 FIXES
- None

### ⚠️ KNOWN ISSUES
- Tray icon is Windows-only (cross-platform support planned for future)
- Pause state resets on agent restart (not persisted to config)
- Log viewer uses system default text editor (may be Notepad on Windows)

### 🚀 DEPLOYMENT NOTES
- Recompiled `fleet_agent.exe` with PyInstaller including pystray and pillow dependencies
- Exe size: 19.7 MB (up from previous due to PIL/pystray libraries)
- No breaking changes to existing API or agent configuration

### 📦 DEPENDENCIES UPDATED
```
pystray>=0.19   # System tray icon library
pillow>=9.0     # PIL for icon rendering
```

---

**Previous versions:** See git history for details on earlier releases.
