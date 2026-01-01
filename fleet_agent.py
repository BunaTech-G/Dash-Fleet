#!/usr/bin/env python3
"""Agent léger qui remonte des métriques vers /api/fleet/report.
- Nécessite psutil.
- Utilise FLEET_TOKEN pour l'authentification.
"""
import argparse
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

import psutil

from fleet_utils import format_bytes_to_gib, format_uptime_hms, calculate_health_score


def get_machine_id() -> str:
    """Retourne un identifiant unique pour la machine (hostname par défaut)."""
    return socket.gethostname()

def collect_agent_stats() -> dict:
    """Collecte les métriques système principales et les retourne sous forme de dict."""
    cpu_percent = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor or "/")
    uptime_seconds = time.time() - psutil.boot_time()

    stats = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cpu_percent": float(cpu_percent),
        "ram_percent": float(ram.percent),
        "ram_used_gib": float(format_bytes_to_gib(ram.used)),
        "ram_total_gib": float(format_bytes_to_gib(ram.total)),
        "disk_percent": float(disk.percent),
        "disk_used_gib": float(format_bytes_to_gib(disk.used)),
        "disk_total_gib": float(format_bytes_to_gib(disk.total)),
        "uptime_seconds": float(uptime_seconds),
        "uptime_hms": format_uptime_hms(uptime_seconds),
    }
    stats["health"] = calculate_health_score(stats)
    # Validation simple des métriques
    for k in ("cpu_percent", "ram_percent", "disk_percent"):
        if not isinstance(stats[k], (int, float)):
            stats[k] = 0.0
    return stats



def post_report(url: str, token: str, machine_id: str, report: dict) -> tuple[bool, str]:
    """Envoie le rapport JSON au serveur, retourne (succès, message)."""
    payload = {"machine_id": machine_id, "report": report}
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            ok = 200 <= resp.getcode() < 300
            return ok, f"HTTP {resp.getcode()}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTPError {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"URLError {exc.reason}"
    except Exception as exc:
        return False, str(exc)



def load_config(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main() -> None:
    """Point d'entrée principal de l'agent."""
    parser = argparse.ArgumentParser(description="Agent de reporting fleet")
    parser.add_argument("--server", default="http://localhost:5000", help="URL du serveur (sans le chemin)")
    parser.add_argument("--path", default="/api/fleet/report", help="Chemin du endpoint")
    parser.add_argument("--interval", type=float, default=10.0, help="Intervalle en secondes")
    parser.add_argument("--token", default=os.environ.get("FLEET_TOKEN", ""), help="FLEET_TOKEN (sinon variable d'env)")
    parser.add_argument("--machine-id", default=get_machine_id(), help="Identifiant machine")
    parser.add_argument("--config", default="config.json", help="Chemin du fichier de configuration JSON")
    parser.add_argument("--log-file", default=None, help="Fichier de log local (optionnel)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    server = args.server if args.server != "http://localhost:5000" else cfg.get("server", args.server)
    path = args.path if args.path != "/api/fleet/report" else cfg.get("path", args.path)
    interval = float(args.interval if args.interval != 10.0 else cfg.get("interval", args.interval))
    machine_id = args.machine_id if args.machine_id != get_machine_id() else cfg.get("machine_id", args.machine_id)

    # Ordre de priorité pour le token : CLI > env > config
    token = args.token or os.environ.get("FLEET_TOKEN") or cfg.get("token", "")
    if not token:
        print("Erreur: FLEET_TOKEN manquant (argument --token, variable d'environnement, ou config.json)")
        raise SystemExit(1)

    log_path = args.log_file or cfg.get("log_file")

    def log_line(msg: str) -> None:
        print(msg)
        if log_path:
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass

    url = server.rstrip("/") + path
    log_line(f"Agent démarré -> {url}")
    log_line(f"id={machine_id}, intervalle={interval}s")

    while True:
        report = collect_agent_stats()
        ok, msg = post_report(url, token, machine_id, report)
        status = "OK" if ok else "KO"
        short = f"CPU {report['cpu_percent']:.1f}% RAM {report['ram_percent']:.1f}% Disk {report['disk_percent']:.1f}%"
        if ok:
            log_line(f"[{time.strftime('%H:%M:%S')}] {status} {msg} | {short} | Score {report['health']['score']}/100")
        else:
            log_line(f"[{time.strftime('%H:%M:%S')}] {status} {msg} | ERREUR d'envoi | {short}")
        # Si le serveur est injoignable, on attend mais on ne quitte pas
        time.sleep(max(1.0, interval))


if __name__ == "__main__":
    main()
