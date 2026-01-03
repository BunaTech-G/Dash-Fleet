#!/usr/bin/env python3
"""
DashFleet - Modern System Metrics & Fleet Management API

Features:
- Clean REST API with proper validation
- Fleet management (collect, store, retrieve agent reports)
- System metrics collection with health scoring
- SQLite persistence
- Background metrics export
- System action execution (Windows-specific)
- Production-ready logging and error handling
"""

import argparse
import csv
import datetime as dt
import json
import logging
import os
import socket
import subprocess
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil
from flask import Flask, jsonify, request, send_file

# ============================================================================
# CONFIGURATION & LOGGING
# ============================================================================

# Create app
app = Flask(__name__, static_folder="static", static_url_path="")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/dashfleet.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Paths
LOGS_DIR = Path("logs")
DATA_DIR = Path("data")
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_HISTORY_CSV = LOGS_DIR / "metrics.csv"
FLEET_DB_PATH = DATA_DIR / "fleet.db"

# Thresholds & Config
CPU_ALERT_THRESHOLD = 80.0
RAM_ALERT_THRESHOLD = 90.0
FLEET_TTL_SECONDS = int(os.environ.get("FLEET_TTL_SECONDS", "600"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_MIN_SECONDS = int(os.environ.get("WEBHOOK_MIN_SECONDS", "300"))

# State
FLEET_STATE: Dict[str, Dict[str, Any]] = {}
_LAST_WEBHOOK_TS = 0.0
_LOCK = threading.Lock()


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


def is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == "nt"


def get_hostname() -> str:
    """Get computer hostname."""
    try:
        return socket.gethostname()
    except Exception as e:
        logger.warning(f"Failed to get hostname: {e}")
        return "unknown"


# ============================================================================
# SYSTEM METRICS
# ============================================================================

def collect_system_metrics() -> Dict[str, Any]:
    """Collect real system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage(get_disk_root())
        uptime_sec = time.time() - psutil.boot_time()
        hostname = get_hostname()

        return {
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
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
            "alerts": {
                "cpu": cpu_percent >= CPU_ALERT_THRESHOLD,
                "ram": ram.percent >= RAM_ALERT_THRESHOLD,
            },
        }
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return {
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
            "hostname": get_hostname(),
            "error": str(e),
        }


def calculate_health_score(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate health score (0-100) and status."""
    if "error" in metrics:
        return {"score": 0, "status": "critical", "components": {}}

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
# DATABASE - FLEET MANAGEMENT
# ============================================================================

def init_db() -> None:
    """Initialize SQLite database."""
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fleet (
                id TEXT PRIMARY KEY,
                hostname TEXT NOT NULL,
                report TEXT NOT NULL,
                ts REAL NOT NULL,
                client TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")


def load_fleet_from_db() -> None:
    """Load fleet state from database."""
    global FLEET_STATE
    try:
        if not FLEET_DB_PATH.exists():
            FLEET_STATE = {}
            return

        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT id, hostname, report, ts, client FROM fleet")
        rows = cur.fetchall()
        conn.close()

        FLEET_STATE = {}
        for mid, hostname, report_json, ts, client in rows:
            try:
                report = json.loads(report_json)
            except json.JSONDecodeError:
                report = {}
            FLEET_STATE[mid] = {
                "id": mid,
                "hostname": hostname,
                "report": report,
                "ts": ts,
                "client": client,
            }

        logger.info(f"Loaded {len(FLEET_STATE)} machines from DB")
    except Exception as e:
        logger.error(f"Failed to load fleet from DB: {e}")
        FLEET_STATE = {}


def save_fleet_to_db() -> None:
    """Save fleet state to database."""
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute("DELETE FROM fleet")

        for mid, entry in FLEET_STATE.items():
            cur.execute(
                "INSERT INTO fleet (id, hostname, report, ts, client) VALUES (?, ?, ?, ?, ?)",
                (
                    mid,
                    entry.get("hostname", "unknown"),
                    json.dumps(entry.get("report", {})),
                    entry.get("ts", 0.0),
                    entry.get("client"),
                ),
            )

        conn.commit()
        conn.close()
        logger.debug(f"Saved {len(FLEET_STATE)} machines to DB")
    except Exception as e:
        logger.error(f"Failed to save fleet to DB: {e}")


def purge_expired_fleet() -> int:
    """Remove expired entries from fleet."""
    global FLEET_STATE
    now_ts = time.time()
    expired_ids = [
        mid
        for mid, entry in FLEET_STATE.items()
        if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS
    ]

    for mid in expired_ids:
        del FLEET_STATE[mid]

    if expired_ids:
        save_fleet_to_db()
        logger.info(f"Purged {len(expired_ids)} expired machines")

    return len(expired_ids)


# ============================================================================
# CSV HISTORY
# ============================================================================

def export_metrics_to_csv(metrics: Dict[str, Any]) -> None:
    """Append metrics to history CSV."""
    if "error" in metrics:
        return

    try:
        LOGS_DIR.mkdir(exist_ok=True)
        file_exists = DEFAULT_HISTORY_CSV.exists()

        with open(DEFAULT_HISTORY_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "hostname",
                    "cpu_percent",
                    "ram_percent",
                    "disk_percent",
                    "uptime_hms",
                    "cpu_alert",
                    "ram_alert",
                ],
            )
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "timestamp": metrics.get("timestamp", ""),
                "hostname": metrics.get("hostname", ""),
                "cpu_percent": metrics.get("cpu_percent", 0),
                "ram_percent": metrics.get("ram_percent", 0),
                "disk_percent": metrics.get("disk_percent", 0),
                "uptime_hms": metrics.get("uptime_hms", ""),
                "cpu_alert": metrics.get("alerts", {}).get("cpu", False),
                "ram_alert": metrics.get("alerts", {}).get("ram", False),
            })
    except Exception as e:
        logger.error(f"Failed to export metrics to CSV: {e}")


def load_history_csv(limit: int = 300) -> List[Dict[str, Any]]:
    """Load last N rows from CSV."""
    if not DEFAULT_HISTORY_CSV.exists():
        return []

    records = []
    try:
        with open(DEFAULT_HISTORY_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    records.append({
                        "timestamp": row.get("timestamp", ""),
                        "hostname": row.get("hostname", ""),
                        "cpu_percent": float(row.get("cpu_percent", 0)),
                        "ram_percent": float(row.get("ram_percent", 0)),
                        "disk_percent": float(row.get("disk_percent", 0)),
                        "uptime_hms": row.get("uptime_hms", ""),
                    })
                except (KeyError, ValueError):
                    continue
    except Exception as e:
        logger.error(f"Failed to load CSV history: {e}")

    return records[-limit:]


# ============================================================================
# WEBHOOK ALERTS
# ============================================================================

def post_webhook(message: str) -> bool:
    """Post to webhook if configured."""
    if not WEBHOOK_URL:
        return False

    try:
        data = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            logger.debug("Webhook posted")
            return True
    except Exception as e:
        logger.warning(f"Failed to post webhook: {e}")
        return False


def maybe_send_alert(metrics: Dict[str, Any], health: Dict[str, Any]) -> None:
    """Send webhook if health is critical."""
    global _LAST_WEBHOOK_TS

    if health.get("status") != "critical":
        return

    now = time.time()
    if now - _LAST_WEBHOOK_TS < WEBHOOK_MIN_SECONDS:
        return

    msg = (
        f"🚨 Critical Health Alert\n"
        f"Score: {health.get('score')}/100\n"
        f"CPU: {metrics.get('cpu_percent', '?')}%\n"
        f"RAM: {metrics.get('ram_percent', '?')}%\n"
        f"Disk: {metrics.get('disk_percent', '?')}%"
    )
    if post_webhook(msg):
        _LAST_WEBHOOK_TS = now


# ============================================================================
# SYSTEM ACTIONS (Windows-only)
# ============================================================================

def run_command(cmd: List[str]) -> Dict[str, Any]:
    """Run shell command safely."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Command timeout", "code": -1}
    except Exception as e:
        return {"ok": False, "error": str(e), "code": -1}


def action_flush_dns() -> Dict[str, Any]:
    """Flush DNS cache (Windows only)."""
    if not is_windows():
        return {"ok": False, "error": "Windows only"}
    return run_command(["ipconfig", "/flushdns"])


def action_restart_spooler() -> Dict[str, Any]:
    """Restart print spooler (Windows only)."""
    if not is_windows():
        return {"ok": False, "error": "Windows only"}
    return run_command(["powershell", "-Command", "Restart-Service -Name Spooler"])


def action_cleanup_temp() -> Dict[str, Any]:
    """Clean temporary files."""
    temp_dir = Path(tempfile.gettempdir())
    deleted = 0
    for path in temp_dir.glob("*.tmp"):
        try:
            path.unlink()
            deleted += 1
        except OSError:
            pass
    return {"ok": True, "message": f"Deleted {deleted} temp files"}


def action_cleanup_teams() -> Dict[str, Any]:
    """Clean Teams cache (Windows only)."""
    if not is_windows():
        return {"ok": False, "error": "Windows only"}

    base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Teams" / "Cache"
    if not base.exists():
        return {"ok": False, "error": "Teams cache not found"}

    deleted = 0
    for path in base.rglob("*"):
        if path.is_file():
            try:
                path.unlink()
                deleted += 1
            except OSError:
                pass
    return {"ok": True, "message": f"Cleaned {deleted} Teams files"}


def action_cleanup_outlook() -> Dict[str, Any]:
    """Clean Outlook cache (Windows only)."""
    if not is_windows():
        return {"ok": False, "error": "Windows only"}

    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Outlook"
    if not base.exists():
        return {"ok": False, "error": "Outlook folder not found"}

    deleted = 0
    for pattern in ("*.tmp", "*.dat"):
        for path in base.rglob(pattern):
            if path.is_file():
                try:
                    path.unlink()
                    deleted += 1
                except OSError:
                    pass
    return {"ok": True, "message": f"Cleaned {deleted} Outlook files"}


def action_collect_logs() -> Dict[str, Any]:
    """Collect diagnostic logs to ZIP."""
    try:
        temp_dir = Path(tempfile.gettempdir())
        zip_path = temp_dir / f"dashfleet_logs_{int(time.time())}.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            metrics = collect_system_metrics()
            zf.writestr("metrics.json", json.dumps(metrics, indent=2))

            if DEFAULT_HISTORY_CSV.exists():
                zf.write(DEFAULT_HISTORY_CSV, arcname="history.csv")

            if is_windows():
                net = run_command(["ipconfig", "/all"])
            else:
                net = run_command(["ifconfig"])
            zf.writestr("network.txt", net.get("stdout", ""))

        return {"ok": True, "message": f"Logs saved to {zip_path}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================================
# API ROUTES
# ============================================================================

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """GET /api/stats - Get current system metrics."""
    try:
        metrics = collect_system_metrics()
        logger.debug("GET /api/stats")
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error in /api/stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def api_status():
    """GET /api/status - Get metrics with health score."""
    try:
        metrics = collect_system_metrics()
        health = calculate_health_score(metrics)
        metrics["health"] = health
        maybe_send_alert(metrics, health)
        logger.debug("GET /api/status")
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error in /api/status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/fleet", methods=["GET"])
def api_fleet():
    """GET /api/fleet - Get all machines in fleet."""
    try:
        with _LOCK:
            purge_expired_fleet()
            data = list(FLEET_STATE.values())
        logger.debug(f"GET /api/fleet -> {len(data)} machines")
        return jsonify({"count": len(data), "data": data}), 200
    except Exception as e:
        logger.error(f"Error in /api/fleet: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/fleet/report", methods=["POST"])
def api_fleet_report():
    """POST /api/fleet/report - Agent reports its metrics."""
    try:
        payload = request.get_json(silent=True) or {}
        machine_id = str(payload.get("machine_id") or "unknown").strip()
        hostname = str(payload.get("hostname") or "unknown").strip()
        report = payload.get("report") or {}

        if not machine_id or machine_id == "unknown":
            logger.warning(f"Fleet report missing machine_id from {request.remote_addr}")
            return jsonify({"error": "machine_id required"}), 400

        now_ts = time.time()

        with _LOCK:
            FLEET_STATE[machine_id] = {
                "id": machine_id,
                "hostname": hostname,
                "report": report,
                "ts": now_ts,
                "client": request.remote_addr,
            }
            save_fleet_to_db()

        logger.info(f"Fleet report from {hostname} ({machine_id}): CPU={report.get('cpu_percent', '?')}%")
        return jsonify({"ok": True}), 200

    except Exception as e:
        logger.error(f"Error in /api/fleet/report: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    """GET /api/history?limit=300 - Get historical metrics."""
    try:
        limit = request.args.get("limit", default="300")
        try:
            limit_int = max(1, min(int(limit), 500))
        except ValueError:
            limit_int = 300

        history = load_history_csv(limit=limit_int)
        logger.debug(f"GET /api/history limit={limit_int} -> {len(history)} rows")
        return jsonify({"count": len(history), "data": history}), 200
    except Exception as e:
        logger.error(f"Error in /api/history: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/action", methods=["POST"])
def api_action():
    """POST /api/action - Execute system action."""
    try:
        payload = request.get_json(silent=True) or {}
        action_name = str(payload.get("action", "")).strip()

        actions = {
            "flush_dns": action_flush_dns,
            "restart_spooler": action_restart_spooler,
            "cleanup_temp": action_cleanup_temp,
            "cleanup_teams": action_cleanup_teams,
            "cleanup_outlook": action_cleanup_outlook,
            "collect_logs": action_collect_logs,
        }

        if action_name not in actions:
            logger.warning(f"Unknown action requested: {action_name}")
            return jsonify({"error": "Unknown action"}), 400

        result = actions[action_name]()
        logger.info(f"Action executed: {action_name} -> ok={result.get('ok')}")
        return jsonify({"action": action_name, **result}), 200

    except Exception as e:
        logger.error(f"Error in /api/action: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# STATIC FILES & SPA
# ============================================================================

@app.route("/")
def serve_app():
    """Serve React SPA."""
    try:
        # Try built app first
        app_path = Path("static/app/index.html")
        if app_path.exists():
            return send_file(str(app_path))
        # Fallback to old structure
        return send_file(Path("static/index.html"))
    except Exception:
        return "Static files not found", 404


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    """Serve static assets (JS, CSS, etc.)."""
    try:
        asset_path = Path("static/app/assets") / filename
        if asset_path.exists():
            return send_file(str(asset_path))
        return "Asset not found", 404
    except Exception as e:
        logger.error(f"Error serving asset {filename}: {e}")
        return "Asset not found", 404


@app.errorhandler(404)
def serve_spa_fallback(e):
    """Fallback to SPA for client-side routing (but not for assets)."""
    # Don't fallback for API routes or assets
    if request.path.startswith('/api/') or request.path.startswith('/assets/'):
        return "Not found", 404
    
    try:
        app_path = Path("static/app/index.html")
        if app_path.exists():
            return send_file(str(app_path))
        return send_file(Path("static/index.html"))
    except Exception:
        return "Not found", 404


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

def background_export_loop(interval: float) -> None:
    """Background thread to export metrics to CSV."""
    logger.info(f"Background export started (interval={interval}s)")
    try:
        while True:
            time.sleep(interval)
            metrics = collect_system_metrics()
            export_metrics_to_csv(metrics)
    except Exception as e:
        logger.error(f"Background export error: {e}")


# ============================================================================
# CLI & MAIN
# ============================================================================

def cli_mode(interval: float) -> None:
    """Run in CLI mode (print metrics)."""
    logger.info("Running in CLI mode")
    try:
        while True:
            metrics = collect_system_metrics()
            health = calculate_health_score(metrics)
            print(
                f"[{metrics.get('timestamp')}] "
                f"CPU={metrics.get('cpu_percent', 0):.1f}% "
                f"RAM={metrics.get('ram_percent', 0):.1f}% "
                f"Disk={metrics.get('disk_percent', 0):.1f}% "
                f"Health={health.get('score', 0)}/100 "
                f"Status={health.get('status', '?')}"
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("CLI mode stopped")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DashFleet - System Metrics & Fleet Management")
    parser.add_argument("--web", action="store_true", help="Run web server")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Web server host")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")), help="Web server port")
    parser.add_argument("--interval", type=float, default=2.0, help="Metrics collection interval (seconds)")
    parser.add_argument("--export", action="store_true", help="Enable background CSV export")

    args = parser.parse_args()

    # Initialize
    init_db()
    load_fleet_from_db()
    logger.info("DashFleet started")

    # Default to web if no mode specified
    if not args.web and not args.cli:
        args.web = True

    # Start background export if requested
    if args.export:
        thread = threading.Thread(target=background_export_loop, args=(args.interval,), daemon=True)
        thread.start()

    # Run selected mode
    if args.web:
        logger.info(f"Starting web server on {args.host}:{args.port}")
        threading.Timer(0.5, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
        app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
    elif args.cli:
        cli_mode(args.interval)


if __name__ == "__main__":
    main()
