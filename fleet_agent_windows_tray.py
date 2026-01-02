"""
Fleet Agent Windows System Tray Support
- Displays system tray icon when agent is running
- Shows real-time metrics in tooltip
- Allows quick status check and configuration

Run with: python fleet_agent.py --server <url> --token <api_key> --tray
"""

import sys
import threading
import time

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


def run_tray_icon(agent_stats_fn):
    """
    Run system tray icon with real-time metrics.
    
    Args:
        agent_stats_fn: Callable that returns stats dict with 'health' key
    """
    if not HAS_PYSTRAY:
        return
    
    if not IS_WINDOWS:
        return

    size = 64

    def create_image(health_status="ok"):
        """Create tray icon image based on health status."""
        img = Image.new("RGB", (size, size), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Color mapping for health status
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

    # Start update thread and tray icon
    update_thread = threading.Thread(target=update_icon, daemon=True)
    update_thread.start()
    
    try:
        icon.run()
    except KeyboardInterrupt:
        icon.stop()

