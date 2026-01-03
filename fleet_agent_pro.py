#!/usr/bin/env python3
"""
DashFleet Agent Pro - Professional system metrics reporter with system tray

Features:
- System tray icon showing agent status
- Auto-start on Windows boot
- Automatic dependency installation
- Professional logging
- Windows and Linux compatibility
"""

import argparse
import datetime as dt
import json
import logging
import os
import socket
import sys
import time
import threading
import urllib.error
import urllib.request
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import psutil, install if missing
try:
    import psutil
except ImportError:
    print("Installing required package: psutil...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

# Try to import pystray for system tray on Windows
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False
    if sys.platform == "win32":
        print("Note: Installing system tray support...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray", "pillow"])
            from pystray import Icon, Menu, MenuItem
            from PIL import Image, ImageDraw
            HAS_TRAY = True
        except:
            HAS_TRAY = False

# ============================================================================
# CONFIGURATION & LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(Path.home() / "dashfleet_agent.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

DEFAULT_SERVER_URL = os.environ.get("DASHFLEET_SERVER", "http://localhost:5000")
DEFAULT_MACHINE_ID = socket.gethostname()
DEFAULT_REPORT_INTERVAL = 30
DEFAULT_API_ENDPOINT = "/api/fleet/report"

CPU_ALERT_THRESHOLD = 80.0
RAM_ALERT_THRESHOLD = 80.0
DISK_ALERT_THRESHOLD = 85.0
MAX_RETRIES = 3
RETRY_DELAY = 5

# Global state
agent_running = True
agent_status = "Starting..."
agent_metrics = {}

# ============================================================================
# METRICS COLLECTION
# ============================================================================

def get_system_metrics() -> Dict[str, Any]:
    """Collect comprehensive system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = dt.datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = int(time.time() - psutil.boot_time())
        uptime_hms = format_uptime(uptime_seconds)
        
        # Calculate health score
        cpu_score = max(0, 100 - cpu_percent)
        ram_score = max(0, 100 - memory.percent)
        disk_score = max(0, 100 - disk.percent)
        health_score = int((cpu_score + ram_score + disk_score) / 3)
        
        # Determine status
        if health_score >= 80:
            status = "ok"
        elif health_score >= 60:
            status = "warn"
        else:
            status = "critical"
        
        return {
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
            "hostname": socket.gethostname(),
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(memory.percent, 1),
            "ram_used_gib": round(memory.used / (1024**3), 2),
            "ram_total_gib": round(memory.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_used_gib": round(disk.used / (1024**3), 1),
            "disk_total_gib": round(disk.total / (1024**3), 1),
            "uptime_seconds": uptime_seconds,
            "uptime_hms": uptime_hms,
            "alerts": {
                "cpu": cpu_percent >= CPU_ALERT_THRESHOLD,
                "ram": memory.percent >= RAM_ALERT_THRESHOLD,
                "disk": disk.percent >= DISK_ALERT_THRESHOLD,
            },
            "alert_active": any([
                cpu_percent >= CPU_ALERT_THRESHOLD,
                memory.percent >= RAM_ALERT_THRESHOLD,
                disk.percent >= DISK_ALERT_THRESHOLD,
            ]),
            "health": {
                "score": health_score,
                "status": status,
                "components": {
                    "cpu": cpu_score,
                    "ram": ram_score,
                    "disk": disk_score,
                },
            },
        }
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return {}

def format_uptime(seconds: int) -> str:
    """Format uptime as HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:02d}"

# ============================================================================
# REPORTING
# ============================================================================

def report_metrics(server_url: str, machine_id: str, metrics: Dict[str, Any]) -> bool:
    """Report metrics to DashFleet server."""
    try:
        url = f"{server_url}{DEFAULT_API_ENDPOINT}"
        payload = {
            "machine_id": machine_id,
            "hostname": machine_id,
            "report": metrics,
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info(f"✓ Reported to {server_url}: {metrics.get('health', {}).get('status', 'unknown')}")
            return True
    except Exception as e:
        logger.error(f"✗ Failed to report: {e}")
        return False

# ============================================================================
# SYSTEM TRAY
# ============================================================================

def create_tray_icon():
    """Create a professional system tray icon."""
    if not HAS_TRAY:
        return None
    
    try:
        # Create a simple icon image (24x24 pixels)
        icon_size = 64
        image = Image.new('RGB', (icon_size, icon_size), color=(15, 20, 25))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple dashboard icon
        draw.rectangle([8, 8, 20, 20], fill=(59, 130, 246))  # Blue square
        draw.rectangle([24, 8, 36, 20], fill=(139, 92, 246))  # Purple square
        draw.rectangle([40, 8, 52, 20], fill=(59, 130, 246))  # Blue square
        draw.rectangle([8, 24, 20, 36], fill=(139, 92, 246))  # Purple square
        draw.rectangle([24, 24, 36, 36], fill=(59, 130, 246))  # Blue square
        draw.rectangle([40, 24, 52, 42], fill=(139, 92, 246))  # Purple tall
        draw.rectangle([8, 40, 52, 52], fill=(59, 130, 246))  # Blue bar
        
        menu = Menu(
            MenuItem("Status: Starting...", None, enabled=False),
            MenuItem("---", None, enabled=False),
            MenuItem("Exit", lambda icon, item: stop_agent()),
        )
        
        icon = Icon("dashfleet_agent", image, menu=menu)
        return icon
    except Exception as e:
        logger.warning(f"Could not create tray icon: {e}")
        return None

def update_tray_status(icon, status: str):
    """Update tray icon status text."""
    if icon:
        try:
            menu = Menu(
                MenuItem(f"Status: {status}", None, enabled=False),
                MenuItem("---", None, enabled=False),
                MenuItem("Exit", lambda icon, item: stop_agent()),
            )
            icon.menu = menu
        except:
            pass

# ============================================================================
# AUTO-START ON WINDOWS
# ============================================================================

def enable_autostart():
    """Register agent to start on Windows boot."""
    if sys.platform != "win32":
        return
    
    try:
        import winreg
        script_path = Path(__file__).resolve()
        pythonw_path = Path(sys.executable).parent / "pythonw.exe"
        
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            cmd = f'"{pythonw_path}" "{script_path}" --server {DEFAULT_SERVER_URL}'
            winreg.SetValueEx(key, "DashFleetAgent", 0, winreg.REG_SZ, cmd)
        logger.info("✓ Auto-start enabled for Windows")
    except Exception as e:
        logger.warning(f"Could not enable auto-start: {e}")

def disable_autostart():
    """Remove agent from Windows auto-start."""
    if sys.platform != "win32":
        return
    
    try:
        import winreg
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "DashFleetAgent")
        logger.info("✓ Auto-start disabled")
    except Exception as e:
        logger.warning(f"Could not disable auto-start: {e}")

# ============================================================================
# AGENT LOOP
# ============================================================================

def stop_agent():
    """Stop the agent gracefully."""
    global agent_running
    agent_running = False
    logger.info("Agent stopping...")
    sys.exit(0)

def run_agent(server_url: str, machine_id: str, interval: int, enable_tray: bool = True):
    """Main agent loop."""
    global agent_running, agent_status, agent_metrics
    
    logger.info(f"DashFleet Agent started")
    logger.info(f"Server: {server_url}")
    logger.info(f"Machine ID: {machine_id}")
    logger.info(f"Report interval: {interval}s")
    
    if enable_tray and HAS_TRAY:
        enable_autostart()
        icon = create_tray_icon()
        if icon:
            def run_icon():
                icon.run()
            icon_thread = threading.Thread(target=run_icon, daemon=True)
            icon_thread.start()
    else:
        icon = None
    
    last_report = 0
    consecutive_failures = 0
    
    while agent_running:
        try:
            now = time.time()
            
            if now - last_report >= interval:
                metrics = get_system_metrics()
                agent_metrics = metrics
                
                if metrics:
                    health_status = metrics.get('health', {}).get('status', 'unknown')
                    agent_status = f"Running - {health_status.upper()}"
                    
                    if report_metrics(server_url, machine_id, metrics):
                        consecutive_failures = 0
                        update_tray_status(icon, agent_status)
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= MAX_RETRIES:
                            logger.warning(f"Failed {MAX_RETRIES} consecutive reports")
                            consecutive_failures = 0
                
                last_report = now
            
            time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)
    
    logger.info("Agent stopped")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="DashFleet Professional Agent - System metrics reporter with system tray"
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER_URL,
        help=f"DashFleet server URL (default: {DEFAULT_SERVER_URL})"
    )
    parser.add_argument(
        "--machine-id",
        default=DEFAULT_MACHINE_ID,
        help=f"Machine ID (default: hostname)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_REPORT_INTERVAL,
        help=f"Report interval in seconds (default: {DEFAULT_REPORT_INTERVAL})"
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Disable system tray icon"
    )
    parser.add_argument(
        "--disable-autostart",
        action="store_true",
        help="Disable auto-start on Windows boot"
    )
    
    args = parser.parse_args()
    
    if args.disable_autostart:
        disable_autostart()
        return
    
    try:
        run_agent(
            server_url=args.server,
            machine_id=args.machine_id,
            interval=args.interval,
            enable_tray=not args.no_tray
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
