"""Simple system dashboard showing CPU, RAM, disk, and uptime.
Run in CLI mode or start a small Flask web UI.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import time
from pathlib import Path
from typing import Dict, Iterable

import psutil
from flask import Flask, jsonify, render_template

# Alert thresholds (percentages).
CPU_ALERT = 80.0
RAM_ALERT = 90.0

app = Flask(__name__, template_folder="templates", static_folder="static")


def _format_bytes_to_gib(bytes_value: float) -> float:
    """Convert bytes to GiB with two decimals."""
    return round(bytes_value / (1024 ** 3), 2)


def _format_uptime(seconds: float) -> str:
    """Return uptime as H:M:S."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _detect_alerts(cpu_percent: float, ram_percent: float) -> Dict[str, bool]:
    return {
        "cpu": cpu_percent >= CPU_ALERT,
        "ram": ram_percent >= RAM_ALERT,
    }


def _disk_usage_target() -> str:
    """Choose a disk mount that works on Windows and Unix."""
    home = Path.home()
    anchor = home.anchor or "/"
    return anchor


def collect_stats() -> Dict[str, object]:
    """Gather the current system metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(_disk_usage_target())
    uptime_seconds = time.time() - psutil.boot_time()

    alerts = _detect_alerts(cpu_percent, ram.percent)

    return {
        "timestamp": dt.datetime.now().isoformat(),
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
    """Append rows to CSV, creating headers when the file is new."""
    fieldnames = [
        "timestamp",
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
    """Append one JSON object per line (JSONL format)."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def print_stats(stats: Dict[str, object]) -> None:
    """Pretty-print stats to the terminal."""
    cpu_flag = " !!" if stats["alerts"]["cpu"] else ""
    ram_flag = " !!" if stats["alerts"]["ram"] else ""
    print(
        f"[{stats['timestamp']}] "
        f"CPU: {stats['cpu_percent']:5.1f}%{cpu_flag} | "
        f"RAM: {stats['ram_percent']:5.1f}% ({stats['ram_used_gib']:.2f}/{stats['ram_total_gib']:.2f} GiB){ram_flag} | "
        f"Disk: {stats['disk_percent']:5.1f}% ({stats['disk_used_gib']:.2f}/{stats['disk_total_gib']:.2f} GiB) | "
        f"Uptime: {stats['uptime_hms']}"
    )


@app.route("/")
def dashboard() -> str:
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    return jsonify(collect_stats())


def run_cli(interval: float, export_csv_path: Path | None, export_json_path: Path | None) -> None:
    print("Monitoring system. Press Ctrl+C to stop. \n")
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="System dashboard: CLI and Flask UI")
    parser.add_argument("--web", action="store_true", help="Start the Flask web dashboard instead of CLI output")
    parser.add_argument("--host", default="127.0.0.1", help="Host for Flask when using --web")
    parser.add_argument("--port", type=int, default=5000, help="Port for Flask when using --web")
    parser.add_argument("--interval", type=float, default=2.0, help="Refresh interval in seconds for CLI mode")
    parser.add_argument("--export-csv", type=Path, help="Path to CSV file for logging snapshots")
    parser.add_argument("--export-jsonl", type=Path, help="Path to JSONL file for logging snapshots")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.web:
        app.run(host=args.host, port=args.port, debug=False)
    else:
        run_cli(args.interval, args.export_csv, args.export_jsonl)


if __name__ == "__main__":
    main()
