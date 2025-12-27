"""Tableau de bord système : CPU, RAM, disque et uptime.
Fonctionne en mode CLI ou via une petite UI web Flask.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict, Iterable

import psutil
from flask import Flask, jsonify, render_template, request

# Seuils d’alerte (pourcentage).
CPU_ALERT = 80.0
RAM_ALERT = 90.0

DEFAULT_HISTORY_CSV = Path("logs/metrics.csv")
DEFAULT_EXPORT_CSV = Path.home() / "Desktop" / "metrics.csv"
DEFAULT_EXPORT_JSONL = Path.home() / "Desktop" / "metrics.jsonl"

app = Flask(__name__, template_folder="templates", static_folder="static")


def _format_bytes_to_gib(bytes_value: float) -> float:
    """Convertit des bytes en Gio avec deux décimales."""
    return round(bytes_value / (1024 ** 3), 2)


def _format_uptime(seconds: float) -> str:
    """Renvoie l’uptime au format H:M:S."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _detect_alerts(cpu_percent: float, ram_percent: float) -> Dict[str, bool]:
    return {
        "cpu": cpu_percent >= CPU_ALERT,
        "ram": ram_percent >= RAM_ALERT,
    }


def _disk_usage_target() -> str:
    """Choisit un point de montage qui fonctionne sous Windows et Unix."""
    home = Path.home()
    anchor = home.anchor or "/"
    return anchor


def collect_stats() -> Dict[str, object]:
    """Récupère les métriques système courantes."""
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
    """Ajoute des lignes dans un CSV, crée l’en-tête si le fichier est nouveau."""
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
    """Ajoute un objet JSON par ligne (format JSONL)."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def load_history(csv_path: Path, limit: int = 200) -> list[Dict[str, object]]:
    """Lit les dernières lignes du CSV d’historique (limite 200 par défaut)."""
    if not csv_path.exists():
        return []

    records: list[Dict[str, object]] = []
    with csv_path.open("r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                records.append({
                    "timestamp": row["timestamp"],
                    "cpu_percent": float(row["cpu_percent"]),
                    "ram_percent": float(row["ram_percent"]),
                    "disk_percent": float(row["disk_percent"]),
                    "uptime_hms": row.get("uptime_hms", ""),
                })
            except (KeyError, ValueError):
                continue

    return records[-limit:]


def print_stats(stats: Dict[str, object]) -> None:
    """Affiche joliment les stats dans le terminal."""
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


@app.route("/history")
def history_page() -> str:
    return render_template("history.html")


@app.route("/api/stats")
def api_stats():
    return jsonify(collect_stats())


@app.route("/api/history")
def api_history():
    limit = request.args.get("limit", default="200")
    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 200

    limit_int = max(1, min(limit_int, 500))
    history = load_history(DEFAULT_HISTORY_CSV, limit=limit_int)
    return jsonify({"count": len(history), "data": history})


def run_cli(interval: float, export_csv_path: Path | None, export_json_path: Path | None) -> None:
    print("Surveillance en cours. Ctrl+C pour arrêter. \n")
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
        print("\nArrêté.")


def start_background_export(interval: float, export_csv_path: Path | None, export_json_path: Path | None) -> None:
    """Démarre un export en tâche de fond pendant que Flask tourne."""

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
    parser = argparse.ArgumentParser(description="Tableau de bord système : CLI et UI Flask")
    parser.add_argument("--web", action="store_true", help="Lancer l’UI web Flask au lieu de la sortie CLI")
    parser.add_argument("--host", default="127.0.0.1", help="Hôte Flask quand --web est activé")
    parser.add_argument("--port", type=int, default=5000, help="Port Flask quand --web est activé")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalle de rafraîchissement en secondes pour le mode CLI")
    parser.add_argument("--export-csv", type=Path, default=DEFAULT_EXPORT_CSV, help="Chemin CSV pour enregistrer les mesures (défaut: Bureau/metrics.csv)")
    parser.add_argument("--export-jsonl", type=Path, default=DEFAULT_EXPORT_JSONL, help="Chemin JSONL pour enregistrer les mesures (défaut: Bureau/metrics.jsonl)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Si lancé par double-clic sans arguments, on bascule en mode web par défaut.
    if len(sys.argv) == 1:
        args.web = True

    if args.web:
        # Si on fournit un export, on lance l’export en tâche de fond en même temps que Flask.
        if args.export_csv or args.export_jsonl:
            start_background_export(args.interval, args.export_csv, args.export_jsonl)
        # Ouvre le navigateur par défaut quelques ms après le démarrage du serveur.
        threading.Timer(0.5, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
        app.run(host=args.host, port=args.port, debug=False)
    else:
        run_cli(args.interval, args.export_csv, args.export_jsonl)


if __name__ == "__main__":
    main()
