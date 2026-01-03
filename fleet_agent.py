#!/usr/bin/env python3
"""
DashFleet Agent - System metrics reporter for DashFleet server

Reports system metrics (CPU, RAM, disk, uptime) to DashFleet server with:
- Automatic hostname detection
- Health score calculation
- Reliable HTTP reporting with retry logic
- Production logging
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
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

# ============================================================================
# CONFIGURATION & LOGGING
# ============================================================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("dashfleet_agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Defaults
DEFAULT_SERVER_URL = os.environ.get("DASHFLEET_SERVER", "http://localhost:5000")
DEFAULT_MACHINE_ID = socket.gethostname()
DEFAULT_REPORT_INTERVAL = 30  # seconds
DEFAULT_API_ENDPOINT = "/api/fleet/report"

# Thresholds for alerts
CPU_ALERT_THRESHOLD = 80.0
RAM_ALERT_THRESHOLD = 90.0


# ============================================================================
# UTILITIES
# ============================================================================

def format_bytes_to_gib(value: float) -> float:
    """Convert bytes to GiB (2 decimal places)."""
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

        return {
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
            "cpu_percent": float(cpu_percent),
            "ram_percent": float(ram.percent),
            "ram_used_gib": format_bytes_to_gib(ram.used),
            "ram_total_gib": format_bytes_to_gib(ram.total),
            "disk_percent": float(disk.percent),
            "disk_used_gib": format_bytes_to_gib(disk.used),
            "disk_total_gib": format_bytes_to_gib(disk.total),
            "uptime_seconds": int(uptime_sec),
            "uptime_hms": format_uptime_hms(uptime_sec),
            "alerts": {
                "cpu": cpu_percent >= CPU_ALERT_THRESHOLD,
                "ram": ram.percent >= RAM_ALERT_THRESHOLD,
            },
        }
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        return {"error": str(e)}


def calculate_health_score(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate health score (0-100)."""
    if "error" in metrics:
        return {"score": 0, "status": "critical"}

    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(metrics.get("cpu_percent", 0))
    ram = float(metrics.get("ram_percent", 0))
    disk = float(metrics.get("disk_percent", 0))

    # Scoring: better at lower resource usage
    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))  # Good if < 50%
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))  # Good if < 60%
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))  # Good if < 70%

    # Weighted average: CPU 35%, RAM 35%, Disk 30%
    overall = cpu_score * 0.35 + ram_score * 0.35 + disk_score * 0.30
    score = round(overall * 100)

    if score >= 80:
        status = "ok"
    elif score >= 60:
        status = "warn"
    else:
        status = "critical"

    return {"score": score, "status": status}


# ============================================================================
# HTTP REPORTING
# ============================================================================

def report_to_server(
    server_url: str,
    machine_id: str,
    hostname: str,
    metrics: Dict[str, Any],
    api_endpoint: str = DEFAULT_API_ENDPOINT,
    timeout: int = 10,
    max_retries: int = 3,
) -> bool:
    """Report metrics to server with retry logic."""
    health = calculate_health_score(metrics)

    payload = {
        "machine_id": machine_id,
        "hostname": hostname,
        "report": {
            **metrics,
            "health": health,
        },
    }

    # Build URL
    if not server_url.startswith("http"):
        server_url = f"http://{server_url}"
    url = server_url.rstrip("/") + api_endpoint

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_retries}: POST {url}")

            # Prepare request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "DashFleet-Agent/1.0",
                },
                method="POST",
            )

            # Send request
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                body = response.read().decode("utf-8")

                if status == 200:
                    logger.info(
                        f"✓ Reported to {url}: "
                        f"CPU={metrics.get('cpu_percent', 0):.1f}% "
                        f"RAM={metrics.get('ram_percent', 0):.1f}% "
                        f"Health={health.get('score', 0)}/100"
                    )
                    return True
                else:
                    last_error = f"HTTP {status}: {body[:100]}"
                    logger.warning(f"Attempt {attempt}: {last_error}")

        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            logger.warning(f"Attempt {attempt}: {last_error}")

        except urllib.error.URLError as e:
            last_error = f"Network error: {e.reason}"
            logger.warning(f"Attempt {attempt}: {last_error}")

        except socket.timeout:
            last_error = f"Timeout ({timeout}s)"
            logger.warning(f"Attempt {attempt}: {last_error}")

        except Exception as e:
            last_error = f"Unexpected error: {type(e).__name__}: {e}"
            logger.error(f"Attempt {attempt}: {last_error}")

        # Wait before retry (exponential backoff)
        if attempt < max_retries:
            wait_time = min(1 + attempt, 10)  # Max 10 seconds
            logger.debug(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

    logger.error(f"✗ Failed to report after {max_retries} attempts: {last_error}")
    return False


# ============================================================================
# MAIN AGENT LOOP
# ============================================================================

def main() -> None:
    """Main agent loop."""
    parser = argparse.ArgumentParser(
        description="DashFleet Agent - Report system metrics to DashFleet server"
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER_URL,
        help=f"DashFleet server URL (default: {DEFAULT_SERVER_URL})",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_API_ENDPOINT,
        help=f"API endpoint path (default: {DEFAULT_API_ENDPOINT})",
    )
    parser.add_argument(
        "--machine-id",
        default=DEFAULT_MACHINE_ID,
        help=f"Machine identifier (default: hostname '{DEFAULT_MACHINE_ID}')",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_REPORT_INTERVAL,
        help=f"Report interval in seconds (default: {DEFAULT_REPORT_INTERVAL}s, min: 5s)",
    )

    args = parser.parse_args()

    # Validate arguments
    interval = max(5, args.interval)  # Minimum 5 seconds
    if interval != args.interval:
        logger.warning(f"Interval adjusted from {args.interval}s to {interval}s (minimum 5s)")

    hostname = get_hostname()
    machine_id = args.machine_id or hostname

    logger.info("=" * 70)
    logger.info("DashFleet Agent Started")
    logger.info(f"  Server:     {args.server}")
    logger.info(f"  Endpoint:   {args.endpoint}")
    logger.info(f"  Machine ID: {machine_id}")
    logger.info(f"  Hostname:   {hostname}")
    logger.info(f"  Interval:   {interval}s")
    logger.info("=" * 70)

    try:
        while True:
            try:
                # Collect and report metrics
                metrics = collect_metrics()

                if "error" in metrics:
                    logger.error(f"Failed to collect metrics: {metrics.get('error')}")
                else:
                    report_to_server(
                        server_url=args.server,
                        machine_id=machine_id,
                        hostname=hostname,
                        metrics=metrics,
                        api_endpoint=args.endpoint,
                    )

                # Wait for next report
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
