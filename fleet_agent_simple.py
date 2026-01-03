#!/usr/bin/env python3
"""
DashFleet Agent Simple - Professional metrics reporter
Clean version without linting errors, ready for PyInstaller compilation
"""

import argparse
import datetime as dt
import json
import logging
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

# Logging configuration
LOG_FILE = str(Path.home() / "dashfleet_agent.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_SERVER_URL = os.environ.get("DASHFLEET_SERVER", "http://localhost:5000")
DEFAULT_MACHINE_ID = socket.gethostname()
DEFAULT_REPORT_INTERVAL = 30
DEFAULT_API_ENDPOINT = "/api/fleet/report"

CPU_ALERT_THRESHOLD = 80.0
RAM_ALERT_THRESHOLD = 80.0
DISK_ALERT_THRESHOLD = 85.0

agent_running = True


def format_uptime(seconds: int) -> str:
    """Format uptime as HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:02d}"


def get_system_metrics() -> Dict[str, Any]:
    """Collect comprehensive system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
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
                    "cpu": int(cpu_score),
                    "ram": int(ram_score),
                    "disk": int(disk_score),
                },
            },
        }
    except (OSError, RuntimeError) as e:
        logger.error("Error collecting metrics: %s", e)
        return {}


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
            response.read()
            health_status = metrics.get('health', {}).get('status', 'unknown')
            logger.info("Reported to %s: %s", server_url, health_status)
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        logger.error("Failed to report: %s", e)
        return False


def stop_agent():
    """Stop the agent gracefully."""
    global agent_running
    agent_running = False
    logger.info("Agent stopping...")
    sys.exit(0)


def run_agent(server_url: str, machine_id: str, interval: int):
    """Main agent loop."""
    global agent_running
    
    logger.info("DashFleet Agent started")
    logger.info("Server: %s", server_url)
    logger.info("Machine ID: %s", machine_id)
    logger.info("Report interval: %ss", interval)
    
    last_report = 0
    consecutive_failures = 0
    max_retries = 3
    
    while agent_running:
        try:
            now = time.time()
            
            if now - last_report >= interval:
                metrics = get_system_metrics()
                
                if metrics:
                    if report_metrics(server_url, machine_id, metrics):
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_retries:
                            logger.warning("Failed %d consecutive reports", max_retries)
                            consecutive_failures = 0
                
                last_report = now
            
            time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            time.sleep(5)
    
    logger.info("Agent stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DashFleet Agent - System metrics reporter"
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER_URL,
        help=f"DashFleet server URL (default: {DEFAULT_SERVER_URL})"
    )
    parser.add_argument(
        "--machine-id",
        default=DEFAULT_MACHINE_ID,
        help="Machine ID (default: hostname)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_REPORT_INTERVAL,
        help=f"Report interval in seconds (default: {DEFAULT_REPORT_INTERVAL})"
    )
    
    args = parser.parse_args()
    
    try:
        run_agent(
            server_url=args.server,
            machine_id=args.machine_id,
            interval=args.interval
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
