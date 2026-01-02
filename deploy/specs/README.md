# PyInstaller .spec Files

Centralized PyInstaller specifications for DashFleet binaries.

## Files

| Spec File | Purpose | Output | Target |
|-----------|---------|--------|--------|
| `server.spec` | Flask server + API | `dashfleet-server` | Windows/Linux |
| `agent.spec` | Fleet monitoring agent | `dashfleet-agent` | Windows/Linux |
| `desktop-gui.spec` | Desktop GUI app | `dashfleet-desktop` | Windows |
| `desktop-cli.spec` | Desktop CLI app | `dashfleet-desktop-console` | Windows |

## Build Commands

### Server Binary
```bash
cd /path/to/DASH-FLEET
pyinstaller deploy/specs/server.spec
# Output: dist/dashfleet-server/
```

### Agent Binary
```bash
pyinstaller deploy/specs/agent.spec
# Output: dist/dashfleet-agent/
```

### Desktop GUI (Windows)
```bash
pyinstaller deploy/specs/desktop-gui.spec
# Output: dist/dashfleet-desktop/dashfleet-desktop.exe
```

### Desktop CLI (Windows)
```bash
pyinstaller deploy/specs/desktop-cli.spec
# Output: dist/dashfleet-desktop-console/dashfleet-desktop-console.exe
```

## Features

- **Portable paths**: Uses relative paths for cross-machine builds
- **Consistent naming**: All binaries have `dashfleet-` prefix
- **Icon support**: All include custom icon.ico
- **Optimized**: UPX compression enabled for smaller sizes

## Notes

- All specs assume icon.ico exists in project root
- Data files (templates/, static/) are embedded in server binary
- Agent spec includes fleet_utils.py in binary
- Desktop specs include templates + static files
