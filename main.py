"""DashFleet Dashboard - System metrics and fleet management.
Simplified version without authentication, organizations, or user management.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import threading
import tempfile
import time
import urllib.error
import urllib.request
import webbrowser
import socket
from pathlib import Path
from typing import Dict, Iterable

import psutil
from flask import Flask, jsonify, request, send_file
import sqlite3

# Configuration
CPU_ALERT = 80.0
RAM_ALERT = 90.0

DEFAULT_HISTORY_CSV = Path("logs/metrics.csv")
DEFAULT_EXPORT_CSV = Path.home() / "Desktop" / "metrics.csv"
DEFAULT_EXPORT_JSONL = Path.home() / "Desktop" / "metrics.jsonl"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_MIN_SECONDS = int(os.environ.get("WEBHOOK_MIN_SECONDS", "300"))
FLEET_TTL_SECONDS = int(os.environ.get("FLEET_TTL_SECONDS", "600"))
FLEET_STATE_PATH = Path("logs/fleet_state.json")
FLEET_DB_PATH = Path("data/fleet.db")

app = Flask(__name__, static_folder="static")

# In-memory fleet state
FLEET_STATE: Dict[str, Dict[str, object]] = {}
_LAST_WEBHOOK_TS = 0.0


def _format_bytes_to_gib(bytes_value: float) -> float:
    """Convert bytes to GiB with 2 decimals."""
    return round(bytes_value / (1024 ** 3), 2)


def _format_uptime(seconds: float) -> str:
    """Format uptime as HH:MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _detect_alerts(cpu_percent: float, ram_percent: float) -> Dict[str, bool]:
    """Detect if thresholds are exceeded."""
    return {
        "cpu": cpu_percent >= CPU_ALERT,
        "ram": ram_percent >= RAM_ALERT,
    }


def _health_score(stats: Dict[str, object]) -> Dict[str, object]:
    """Calculate health score 0-100 and status (ok/warn/critical)."""
    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(stats["cpu_percent"])
    ram = float(stats["ram_percent"])
    disk = float(stats["disk_percent"])

    # Component scores (1 = perfect, 0 = bad)
    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))

    # Weighted average
    weights = {"cpu": 0.35, "ram": 0.35, "disk": 0.30}
    overall = (
        cpu_score * weights["cpu"]
        + ram_score * weights["ram"]
        + disk_score * weights["disk"]
    )

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


def _get_disk_target() -> str:
    """Get root directory for disk usage."""
    home = Path.home()
    return home.anchor or "/"


def _is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == "nt"


def _post_webhook(message: str) -> bool:
    """Post message to webhook."""
    if not WEBHOOK_URL:
        return False
    data = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            return True
    except urllib.error.URLError:
        return False


def _get_hostname() -> str:
    """Get computer hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def collect_stats() -> Dict[str, object]:
    """Collect current system metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(_get_disk_target())
    uptime_seconds = time.time() - psutil.boot_time()

    alerts = _detect_alerts(cpu_percent, ram.percent)

    return {
        "timestamp": dt.datetime.now().isoformat(),
        "hostname": _get_hostname(),
        "cpu_percent": cpu_percent,
        "ram_percent": ram.percent,
        "ram_used_gib": _format_bytes_to_gib(ram.used),
        "ram_total_gib": _format_bytes_to_gib(ram.total),
        "disk_percent": disk.percent,
        "disk_used_gib": _format_bytes_to_gib(disk.used),
        "disk_total_gib": _format_bytes_to_gib(disk.total),
        "uptime_seconds": uptime_seconds,
        "uptime_hms": _format_uptime(uptime_seconds),
        "alerts": alerts,
        "alert_active": any(alerts.values()),
    }


def export_to_csv(csv_path: Path, rows: Iterable[Dict[str, object]]) -> None:
    """Append rows to CSV file."""
    fieldnames = [
        "timestamp",
        "hostname",
        "cpu_percent",
        "ram_percent",
        "ram_used_gib",
        "ram_total_gib",
        "disk_percent",
        "disk_used_gib",
        "disk_total_gib",
        "uptime_seconds",
        "uptime_hms",
        "cpu_alert",
        "ram_alert",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()

    with csv_path.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({
                "timestamp": row["timestamp"],
                "hostname": row.get("hostname", "unknown"),
                "cpu_percent": row["cpu_percent"],
                "ram_percent": row["ram_percent"],
                "ram_used_gib": row["ram_used_gib"],
                "ram_total_gib": row["ram_total_gib"],
                "disk_percent": row["disk_percent"],
                "disk_used_gib": row["disk_used_gib"],
                "disk_total_gib": row["disk_total_gib"],
                "uptime_seconds": row["uptime_seconds"],
                "uptime_hms": row["uptime_hms"],
                "cpu_alert": row["alerts"]["cpu"],
                "ram_alert": row["alerts"]["ram"],
            })


def export_to_jsonl(jsonl_path: Path, rows: Iterable[Dict[str, object]]) -> None:
    """Append rows as JSONL."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def load_history(csv_path: Path, limit: int = 200) -> list[Dict[str, object]]:
    """Load last N rows from history CSV."""
    if not csv_path.exists():
        return []

    records: list[Dict[str, object]] = []
    with csv_path.open("r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                records.append({
                    "timestamp": row["timestamp"],
                    "hostname": row.get("hostname", "unknown"),
                    "cpu_percent": float(row["cpu_percent"]),
                    "ram_percent": float(row["ram_percent"]),
                    "disk_percent": float(row["disk_percent"]),
                    "uptime_hms": row.get("uptime_hms", ""),
                })
            except (KeyError, ValueError):
                continue

    return records[-limit:]


def _run_subprocess(cmd: list[str]) -> Dict[str, object]:
    """Run subprocess and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "ok": result.returncode == 0,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "code": result.returncode,
        }
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "code": -1}


def _action_flush_dns() -> Dict[str, object]:
    """Flush DNS cache (Windows only)."""
    if not _is_windows():
        return {"ok": False, "message": "Windows only"}
    return _run_subprocess(["ipconfig", "/flushdns"])


def _action_restart_spooler() -> Dict[str, object]:
    """Restart print spooler (Windows only)."""
    if not _is_windows():
        return {"ok": False, "message": "Windows only"}
    return _run_subprocess(["powershell", "-Command", "Restart-Service -Name Spooler"])


def _action_cleanup_temp() -> Dict[str, object]:
    """Clean temporary files."""
    temp_dir = Path(tempfile.gettempdir())
    deleted = 0
    for path in temp_dir.glob("*.tmp"):
        try:
            path.unlink()
            deleted += 1
        except OSError:
            continue
    return {"ok": True, "message": f"Deleted {deleted} .tmp files"}


def _action_cleanup_teams() -> Dict[str, object]:
    """Clean Teams cache (Windows only)."""
    if not _is_windows():
        return {"ok": False, "message": "Windows only"}
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Teams" / "Cache"
    if not base.exists():
        return {"ok": False, "message": "Teams cache not found"}

    deleted = 0
    for path in base.rglob("*"):
        if path.is_file():
            try:
                path.unlink()
                deleted += 1
            except OSError:
                continue
    return {"ok": True, "message": f"Cleaned {deleted} files"}


def _action_cleanup_outlook() -> Dict[str, object]:
    """Clean Outlook cache (Windows only)."""
    if not _is_windows():
        return {"ok": False, "message": "Windows only"}
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Outlook"
    if not base.exists():
        return {"ok": False, "message": "Outlook folder not found"}

    deleted = 0
    for pattern in ("*.tmp", "*.dat"):
        for path in base.rglob(pattern):
            if path.is_file():
                try:
                    path.unlink()
                    deleted += 1
                except OSError:
                    continue
    return {"ok": True, "message": f"Cleaned {deleted} files"}


def _action_collect_logs() -> Dict[str, object]:
    """Collect system logs to ZIP."""
    import zipfile
    temp_dir = Path(tempfile.gettempdir())
    zip_path = temp_dir / f"diag_logs_{int(time.time())}.zip"

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            stats = collect_stats()
            zf.writestr("stats.json", json.dumps(stats, indent=2))

            if DEFAULT_HISTORY_CSV.exists():
                zf.write(DEFAULT_HISTORY_CSV, arcname="metrics.csv")

            if _is_windows():
                net = _run_subprocess(["ipconfig", "/all"])
            else:
                net = _run_subprocess(["ifconfig"])
            zf.writestr("network.txt", net.get("stdout", ""))

        return {"ok": True, "message": f"Logs collected: {zip_path}"}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def _maybe_send_webhook(stats: Dict[str, object]) -> None:
    """Send webhook if health is critical."""
    global _LAST_WEBHOOK_TS
    if not WEBHOOK_URL:
        return
    health = stats.get("health") or {}
    status = health.get("status", "ok")
    score = health.get("score", 100)
    if status != "critical":
        return

    now = time.time()
    if now - _LAST_WEBHOOK_TS < WEBHOOK_MIN_SECONDS:
        return

    msg = (
        f"Critical health alert: score={score}/100, "
        f"CPU={stats.get('cpu_percent', '?')}%, "
        f"RAM={stats.get('ram_percent', '?')}%, "
        f"Disk={stats.get('disk_percent', '?')}%"
    )
    sent = _post_webhook(msg)
    if sent:
        _LAST_WEBHOOK_TS = now


def _ensure_db_schema() -> None:
    """Ensure database tables exist."""
    try:
        FLEET_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS fleet '
            '(id TEXT PRIMARY KEY, hostname TEXT, report TEXT, ts REAL, client TEXT)'
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _load_fleet_state() -> None:
    """Load fleet state from database and JSON backup."""
    global FLEET_STATE
    
    # Try database first
    try:
        if FLEET_DB_PATH.exists():
            conn = sqlite3.connect(str(FLEET_DB_PATH))
            cur = conn.cursor()
            cur.execute("SELECT id, hostname, report, ts, client FROM fleet")
            rows = cur.fetchall()
            conn.close()
            FLEET_STATE = {}
            for rid, hostname, report_json, ts, client in rows:
                try:
                    report = json.loads(report_json) if report_json else {}
                except Exception:
                    report = {}
                FLEET_STATE[str(rid)] = {
                    "id": str(rid),
                    "hostname": hostname,
                    "report": report,
                    "ts": ts or 0,
                    "client": client,
                }
            # Purge expired
            now_ts = time.time()
            expired = [mid for mid, entry in FLEET_STATE.items() if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS]
            for mid in expired:
                FLEET_STATE.pop(mid, None)
            if expired:
                _save_fleet_state()
            return
    except Exception:
        pass

    # Fallback to JSON
    if not FLEET_STATE_PATH.exists():
        FLEET_STATE = {}
        return
    try:
        data = json.loads(FLEET_STATE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            FLEET_STATE = {str(k): v for k, v in data.items()}
            now_ts = time.time()
            expired = [mid for mid, entry in FLEET_STATE.items() if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS]
            for mid in expired:
                FLEET_STATE.pop(mid, None)
            if expired:
                _save_fleet_state()
    except (OSError, json.JSONDecodeError):
        FLEET_STATE = {}


def _save_fleet_state() -> None:
    """Save fleet state to database and JSON backup."""
    try:
        # JSON backup
        FLEET_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            FLEET_STATE_PATH.write_text(json.dumps(FLEET_STATE), encoding="utf-8")
        except OSError:
            pass

        # Database
        try:
            FLEET_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(FLEET_DB_PATH))
            cur = conn.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS fleet '
                        '(id TEXT PRIMARY KEY, hostname TEXT, report TEXT, ts REAL, client TEXT)')
            for mid, entry in FLEET_STATE.items():
                report_json = json.dumps(entry.get('report', {}), ensure_ascii=False)
                hostname = entry.get('hostname', 'unknown')
                ts = entry.get('ts', time.time())
                client = entry.get('client')
                cur.execute(
                    'INSERT OR REPLACE INTO fleet (id, hostname, report, ts, client) VALUES (?, ?, ?, ?, ?)',
                    (str(mid), hostname, report_json, ts, client),
                )
            conn.commit()
            conn.close()
        except Exception:
            pass
    except Exception:
        pass


def print_stats(stats: Dict[str, object]) -> None:
    """Pretty print stats to console."""
    cpu_flag = " !!" if stats["alerts"]["cpu"] else ""
    ram_flag = " !!" if stats["alerts"]["ram"] else ""
    print(
        f"[{stats['timestamp']}] {stats.get('hostname', 'unknown')} | "
        f"CPU: {stats['cpu_percent']:5.1f}%{cpu_flag} | "
        f"RAM: {stats['ram_percent']:5.1f}% ({stats['ram_used_gib']:.2f}/{stats['ram_total_gib']:.2f} GiB){ram_flag} | "
        f"Disk: {stats['disk_percent']:5.1f}% ({stats['disk_used_gib']:.2f}/{stats['disk_total_gib']:.2f} GiB) | "
        f"Uptime: {stats['uptime_hms']}"
    )


# ============================================================================
# ROUTES - Frontend
# ============================================================================

@app.route("/")
def dashboard() -> object:
    """Serve SPA or fallback template."""
    index_path = Path("static/app/index.html")
    if index_path.exists():
        try:
            return send_file(str(index_path))
        except Exception:
            pass
    return send_file(Path("static/index.html"))


# ============================================================================
# ROUTES - API
# ============================================================================

@app.route("/api/stats")
def api_stats():
    """Get current system stats."""
    return jsonify(collect_stats())


@app.route("/api/status")
def api_status():
    """Get current status with health score."""
    stats = collect_stats()
    stats["health"] = _health_score(stats)
    _maybe_send_webhook(stats)
    return jsonify(stats)


@app.route("/api/history")
def api_history():
    """Get history data."""
    limit = request.args.get("limit", default="200")
    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 200

    limit_int = max(1, min(limit_int, 500))
    history = load_history(DEFAULT_HISTORY_CSV, limit=limit_int)
    return jsonify({"count": len(history), "data": history})


@app.route("/api/fleet")
def api_fleet():
    """Get fleet data (all machines)."""
    # Purge expired entries
    now_ts = time.time()
    expired = [mid for mid, entry in list(FLEET_STATE.items()) if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS]
    for mid in expired:
        FLEET_STATE.pop(mid, None)
    if expired:
        _save_fleet_state()

    data = list(FLEET_STATE.values())
    return jsonify({"count": len(data), "data": data})


@app.route("/api/fleet/report", methods=["POST"])
def api_fleet_report():
    """Agent reports its metrics."""
    payload = request.get_json(silent=True) or {}
    machine_id = str(payload.get("machine_id") or payload.get("id") or "unknown")
    hostname = str(payload.get("hostname") or "unknown")
    report = payload.get("report") or {}
    now_ts = time.time()

    FLEET_STATE[machine_id] = {
        "id": machine_id,
        "hostname": hostname,
        "report": report,
        "ts": now_ts,
        "client": request.remote_addr,
    }

    _save_fleet_state()
    return jsonify({"ok": True})


@app.route("/api/action", methods=["POST"])
def api_action():
    """Run approved action."""
    payload = request.get_json(silent=True) or {}
    action_name = str(payload.get("action", "")).strip()

    actions = {
        "flush_dns": _action_flush_dns,
        "restart_spooler": _action_restart_spooler,
        "cleanup_temp": _action_cleanup_temp,
        "cleanup_teams": _action_cleanup_teams,
        "cleanup_outlook": _action_cleanup_outlook,
        "collect_logs": _action_collect_logs,
    }

    if action_name not in actions:
        return jsonify({"error": "Unknown action"}), 400

    result = actions[action_name]()
    return jsonify({"action": action_name, **result})


# ============================================================================
# CLI and Background Tasks
# ============================================================================

def run_cli(interval: float, export_csv_path: Path | None, export_json_path: Path | None) -> None:
    """Run in CLI mode."""
    print("Monitoring... Press Ctrl+C to stop.\n")
    try:
        while True:
            stats = collect_stats()
            print_stats(stats)

            if export_csv_path:
                export_to_csv(export_csv_path, [stats])
            if export_json_path:
                export_to_jsonl(export_json_path, [stats])

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")


def start_background_export(interval: float, export_csv_path: Path | None, export_json_path: Path | None) -> None:
    """Start background export thread."""
    def _loop() -> None:
        while True:
            stats = collect_stats()
            if export_csv_path:
                export_to_csv(export_csv_path, [stats])
            if export_json_path:
                export_to_jsonl(export_json_path, [stats])
            time.sleep(interval)

    if not export_csv_path and not export_json_path:
        return

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="DashFleet - System Dashboard")
    parser.add_argument("--web", action="store_true", help="Launch web UI")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Flask host")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")), help="Flask port")
    parser.add_argument("--interval", type=float, default=2.0, help="Refresh interval in CLI mode")
    parser.add_argument(
        "--export-csv",
        type=Path,
        default=DEFAULT_EXPORT_CSV,
        help="CSV export path",
    )
    parser.add_argument(
        "--export-jsonl",
        type=Path,
        default=DEFAULT_EXPORT_JSONL,
        help="JSONL export path",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    _ensure_db_schema()
    _load_fleet_state()

    # Default to web mode if no args
    if len(sys.argv) == 1:
        args.web = True

    if args.web:
        if args.export_csv or args.export_jsonl:
            start_background_export(args.interval, args.export_csv, args.export_jsonl)
        threading.Timer(0.5, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
        app.run(host=args.host, port=args.port, debug=False)
    else:
        run_cli(args.interval, args.export_csv, args.export_jsonl)


if __name__ == "__main__":
    main()
