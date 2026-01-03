#!/usr/bin/env python3
"""
DashFleet Agent - Lightweight system metrics reporter

Reports system metrics to the DashFleet server via HTTP POST.
Features:
- Real system metrics (CPU, RAM, disk, uptime)
- Health scoring
- Reliable HTTP reporting with retry logic
- Clean logging
- Windows/Linux compatible
"""

import argparse
import json
import logging
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("dashfleet_agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# UTILITIES
# ============================================================================

def format_bytes_to_gib(value: float) -> float:
    """Convert bytes to GiB."""
    return round(value / (1024 ** 3), 2)


def format_uptime_hms(seconds: float) -> str:
    """Format seconds to HH:MM:SS."""
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_disk_root() -> str:
    """Get disk root (Windows: C:/, Unix: /)."""
    return Path.home().anchor or "/"


def get_hostname() -> str:
    """Get computer hostname."""
    try:
        return socket.gethostname()
    except Exception as e:
        logger.warning(f"Failed to get hostname: {e}")
        return "unknown"


# ============================================================================
# METRICS COLLECTION
# ============================================================================

def collect_metrics() -> Dict[str, Any]:
    """Collect system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage(get_disk_root())
        uptime_sec = time.time() - psutil.boot_time()
        hostname = get_hostname()

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hostname": hostname,
            "cpu_percent": float(cpu_percent),
            "ram_percent": float(ram.percent),
            "ram_used_gib": format_bytes_to_gib(ram.used),
            "ram_total_gib": format_bytes_to_gib(ram.total),
            "disk_percent": float(disk.percent),
            "disk_used_gib": format_bytes_to_gib(disk.used),
            "disk_total_gib": format_bytes_to_gib(disk.total),
            "uptime_seconds": int(uptime_sec),
            "uptime_hms": format_uptime_hms(uptime_sec),
        }
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hostname": get_hostname(),
            "error": str(e),
        }


def calculate_health_score(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate health score (0-100) and status."""
    if "error" in metrics:
        return {"score": 0, "status": "critical"}

    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(metrics.get("cpu_percent", 0))
    ram = float(metrics.get("ram_percent", 0))
    disk = float(metrics.get("disk_percent", 0))

    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))

    overall = cpu_score * 0.35 + ram_score * 0.35 + disk_score * 0.30
    score = round(overall * 100)

    if score >= 80:
        status = "ok"
    elif score >= 60:
        status = "warn"
    else:
        status = "critical"

    return {
        "score": score,
        "status": status,
        "components": {
            "cpu": round(cpu_score * 100),
            "ram": round(ram_score * 100),
            "disk": round(disk_score * 100),
        },
    }


# ============================================================================
# HTTP REPORTING
# ============================================================================

def report_to_server(
    server_url: str,
    machine_id: str,
    report: Dict[str, Any],
    max_retries: int = 3,
) -> Tuple[bool, str]:
    """
    Report metrics to server with retry logic.
    
    Returns: (success: bool, message: str)
    """
    payload = {
        "machine_id": machine_id,
        "hostname": report.get("hostname", "unknown"),
        "report": report,
    }

    for attempt in range(1, max_retries + 1):
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                server_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.getcode()
                if 200 <= status_code < 300:
                    return True, f"HTTP {status_code}"
                else:
                    return False, f"HTTP {status_code}"

        except urllib.error.HTTPError as e:
            msg = f"HTTPError {e.code}"
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {msg}, retrying...")
                time.sleep(1)
            else:
                return False, msg

        except urllib.error.URLError as e:
            msg = f"URLError {e.reason}"
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {msg}, retrying...")
                time.sleep(2)
            else:
                return False, msg

        except Exception as e:
            msg = str(e)
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {msg}, retrying...")
                time.sleep(1)
            else:
                return False, msg

    return False, "Max retries exceeded"


# ============================================================================
# MAIN LOOP
# ============================================================================

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DashFleet Agent - System Metrics Reporter"
    )
    parser.add_argument(
        "--server",
        default=os.environ.get("DASHFLEET_SERVER", "http://localhost:5000"),
        help="Server URL (e.g., http://localhost:5000 or https://dash-fleet.com)",
    )
    parser.add_argument(
        "--endpoint",
        default="/api/fleet/report",
        help="API endpoint path",
    )
    parser.add_argument(
        "--machine-id",
        default=get_hostname(),
        help="Machine ID (default: hostname)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Report interval in seconds",
    )

    args = parser.parse_args()

    # Validate inputs
    machine_id = str(args.machine_id).strip()
    if not machine_id or machine_id == "unknown":
        logger.error("Invalid machine-id")
        sys.exit(1)

    server_url = args.server.rstrip("/") + args.endpoint
    interval = max(5.0, args.interval)

    logger.info(
        f"Agent started: server={args.server}, "
        f"machine_id={machine_id}, interval={interval}s"
    )

    # Main loop
    try:
        while True:
            try:
                metrics = collect_metrics()
                
                if "error" not in metrics:
                    health = calculate_health_score(metrics)
                    metrics["health"] = health

                ok, msg = report_to_server(server_url, machine_id, metrics)

                status = "✓" if ok else "✗"
                cpu = metrics.get("cpu_percent", "?")
                ram = metrics.get("ram_percent", "?")
                disk = metrics.get("disk_percent", "?")
                health_score = metrics.get("health", {}).get("score", "?")

                logger.info(
                    f"{status} {msg} | "
                    f"CPU {cpu}% RAM {ram}% Disk {disk}% Health {health_score}/100"
                )

            except Exception as e:
                logger.error(f"Reporting loop error: {e}")

            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
