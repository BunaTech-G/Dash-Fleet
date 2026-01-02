"""
Fleet Agent Windows System Tray Support
- Displays system tray icon when agent is running
- Shows real-time metrics in tooltip
- Allows pause/resume/logs/quit from context menu

Run with: python fleet_agent.py --server <url> --token <api_key> --tray
"""

import logging
import os
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
        logging.warning("pystray/pillow not installed. Install with: pip install pystray pillow")
else:
    HAS_PYSTRAY = False


class TrayAgent:
    """Manages system tray icon state and controls."""
    
    def __init__(self, machine_id: str = "DashFleet", log_file: str = None):
        self.machine_id = machine_id
        self.log_file = log_file
        self.paused = False
        self.lock = threading.Lock()
        self.icon = None
    
    def is_paused(self) -> bool:
        """Check if agent is paused."""
        with self.lock:
            return self.paused
    
    def set_paused(self, paused: bool) -> None:
        """Set pause state."""
        with self.lock:
            self.paused = paused
    
    def on_pause(self, icon, item):
        """Pause agent callback."""
        self.set_paused(True)
        logging.info("Agent paused via tray menu")
    
    def on_resume(self, icon, item):
        """Resume agent callback."""
        self.set_paused(False)
        logging.info("Agent resumed via tray menu")
    
    def on_view_logs(self, icon, item):
        """Open logs in default editor."""
        if not self.log_file or not Path(self.log_file).exists():
            logging.warning(f"Log file not found: {self.log_file}")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(self.log_file)
            elif sys.platform == "darwin":
                os.system(f"open '{self.log_file}'")
            else:
                os.system(f"xdg-open '{self.log_file}'")
            logging.info(f"Opened log file: {self.log_file}")
        except Exception as e:
            logging.error(f"Could not open log file: {e}")
    
    def on_quit(self, icon, item):
        """Quit agent callback."""
        logging.info("Agent quit via tray menu")
        if icon:
            icon.stop()
        sys.exit(0)


def run_tray_icon(agent_stats_fn, machine_id: str = "DashFleet", log_file: str = None):
    """
    Run system tray icon with real-time metrics and controls.
    
    Args:
        agent_stats_fn: Callable that returns stats dict with 'health' key
        machine_id: Machine identifier for display
        log_file: Optional path to agent log file
    """
    if not HAS_PYSTRAY or not IS_WINDOWS:
        logging.warning("Tray icon not available on this platform")
        return
    
    tray_agent = TrayAgent(machine_id=machine_id, log_file=log_file)
    size = 64

    def create_image(health_status="ok", paused=False):
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
        if paused:
            # Desaturate color when paused
            r, g, b = color
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            color = (gray, gray, gray)
        
        # Draw circle (status indicator)
        margin = 8
        draw.ellipse([margin, margin, size-margin, size-margin], fill=color)
        
        # Draw border
        draw.rectangle([0, 0, size-1, size-1], outline=(128, 128, 128), width=2)
        
        # Draw pause indicator if paused
        if paused:
            bar_width = 4
            bar_height = 20
            x_offset = 18
            y_offset = 22
            draw.rectangle([x_offset, y_offset, x_offset+bar_width, y_offset+bar_height], fill=(200, 0, 0))
            draw.rectangle([x_offset+8, y_offset, x_offset+8+bar_width, y_offset+bar_height], fill=(200, 0, 0))
        
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
            paused_status = "PAUSED" if tray_agent.is_paused() else "ONLINE"
            
            return (
                f"DashFleet Agent\n"
                f"━━━━━━━━━━━━━\n"
                f"Status: {paused_status}\n"
                f"Health Score: {score:.0f}/100\n"
                f"━━━━━━━━━━━━━\n"
                f"CPU: {cpu:.1f}%\n"
                f"RAM: {ram:.1f}%\n"
                f"Disk: {disk:.1f}%"
            )
        except Exception as e:
            logging.debug(f"Tooltip error: {e}")
            return "DashFleet Agent\nLoading metrics..."

    def build_menu():
        """Build dynamic menu based on pause state."""
        paused = tray_agent.is_paused()
        
        if paused:
            pause_item = MenuItem("▶️  Resume Agent", tray_agent.on_resume)
        else:
            pause_item = MenuItem("⏸️  Pause Agent", tray_agent.on_pause)
        
        menu_items = [
            MenuItem(f"🖥️  {machine_id}", lambda i, x: None, enabled=False),
            Menu.SEPARATOR,
            pause_item,
        ]
        
        if log_file:
            menu_items.append(MenuItem("📋 View Logs", tray_agent.on_view_logs))
        
        menu_items.extend([
            Menu.SEPARATOR,
            MenuItem("❌ Quit", tray_agent.on_quit),
        ])
        
        return Menu(*menu_items)

    # Create tray icon
    try:
        tray_agent.icon = Icon(
            "DashFleet",
            create_image("ok", False),
            title="DashFleet Agent",
            menu=build_menu()
        )

        # Update icon in background
        def update_icon():
            while True:
                try:
                    if not tray_agent.icon or not tray_agent.icon.visible:
                        break
                    
                    stats = agent_stats_fn()
                    health = stats.get("health", {})
                    status = health.get("status", "ok")
                    paused = tray_agent.is_paused()
                    
                    tray_agent.icon.icon = create_image(status, paused)
                    tray_agent.icon.title = get_tooltip_text()
                    tray_agent.icon.menu = build_menu()
                except Exception as e:
                    logging.debug(f"Tray update error: {e}")
                
                time.sleep(5)

        # Start update thread and tray icon
        update_thread = threading.Thread(target=update_icon, daemon=True)
        update_thread.start()
        
        logging.info(f"DashFleet tray icon started for {machine_id}")
        tray_agent.icon.run()
    except Exception as e:
        logging.error(f"Tray icon error: {e}")


__all__ = ["run_tray_icon", "TrayAgent"]

