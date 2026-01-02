"""
Fleet Agent Windows System Tray Support
- Displays system tray icon when agent is running
- Shows real-time metrics in tooltip
- Allows quick status check and configuration

Run with: python fleet_agent_windows_tray.py --server <url> --token <api_key> --tray
"""

import sys
import threading
import time
from pathlib import Path

# Check if running on Windows
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    try:
        from pystray import Icon, Menu, MenuItem
        from PIL import Image, ImageDraw
        HAS_PYSTRAY = True
    except ImportError:
        HAS_PYSTRAY = False
        print("Warning: pystray/pillow not installed. Install with: pip install pystray pillow")
else:
    HAS_PYSTRAY = False


def create_tray_icon(agent_stats_fn):
    """Create and display system tray icon with real-time metrics."""
    if not HAS_PYSTRAY or not IS_WINDOWS:
        return None

    # Create icon image (simple colored square with status indicator)
    def create_image(health_status="ok"):
        size = 64
        img = Image.new("RGB", (size, size), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Status colors
        colors = {
            "ok": (34, 197, 94),        # Green
            "warn": (250, 204, 21),     # Yellow
            "critical": (244, 63, 94),  # Red
            "offline": (156, 163, 175)  # Gray
        }
        
        color = colors.get(health_status, colors["ok"])
        
        # Draw circle (status indicator)
        margin = 8
        draw.ellipse([margin, margin, size-margin, size-margin], fill=color)
        
        # Draw border
        draw.rectangle([0, 0, size-1, size-1], outline=(128, 128, 128), width=2)
        
        return img

    def get_tooltip_text():
        """Get current metrics for tooltip."""
        try:
            stats = agent_stats_fn()
            cpu = stats.get("cpu_percent", 0)
            ram = stats.get("ram_percent", 0)
            disk = stats.get("disk_percent", 0)
            health = stats.get("health", {})
            status = health.get("status", "ok")
            score = health.get("score", 0)
            
            return (
                f"DashFleet Agent\n"
                f"━━━━━━━━━━━━━\n"
                f"Status: {status.upper()}\n"
                f"Health Score: {score}/100\n"
                f"━━━━━━━━━━━━━\n"
                f"CPU: {cpu:.1f}%\n"
                f"RAM: {ram:.1f}%\n"
                f"Disk: {disk:.1f}%"
            )
        except Exception:
            return "DashFleet Agent\nLoading metrics..."

    def on_quit(icon, item):
        """Callback for quit menu item."""
        icon.stop()
        sys.exit(0)

    # Create tray icon
    icon = Icon(
        "DashFleet",
        create_image("ok"),
        menu=Menu(
            MenuItem("DashFleet Agent", lambda: None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Quit", on_quit),
        )
    )

    # Update icon in background
    def update_icon():
        while icon.visible:
            try:
                stats = agent_stats_fn()
                health = stats.get("health", {})
                status = health.get("status", "ok")
                icon.icon = create_image(status)
                icon.title = get_tooltip_text()
            except Exception:
                pass
            time.sleep(5)

    # Start update thread
    update_thread = threading.Thread(target=update_icon, daemon=True)
    update_thread.start()

    return icon


def run_tray_icon(agent_stats_fn):
    """Run system tray icon (blocking call, run in separate thread)."""
    if not HAS_PYSTRAY or not IS_WINDOWS:
        print("System tray icon requires Windows and pystray/pillow packages")
        return

    icon = create_tray_icon(agent_stats_fn)
    if icon:
        icon.run()
