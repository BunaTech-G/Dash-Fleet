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


def _format_bytes_to_gib(value: float) -> float:
    return round(value / (1024 ** 3), 2)


def _format_hms(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _health_score(stats: dict) -> dict:
    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(stats["cpu_percent"])
    ram = float(stats["ram_percent"])
    disk = float(stats["disk_percent"])

    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))

    weights = {"cpu": 0.35, "ram": 0.35, "disk": 0.30}
    overall = cpu_score * weights["cpu"] + ram_score * weights["ram"] + disk_score * weights["disk"]

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
        "ram_used_gib": float(_format_bytes_to_gib(ram.used)),
        "ram_total_gib": float(_format_bytes_to_gib(ram.total)),
        "disk_percent": float(disk.percent),
        "disk_used_gib": float(_format_bytes_to_gib(disk.used)),
        "disk_total_gib": float(_format_bytes_to_gib(disk.total)),
        "uptime_seconds": float(uptime_seconds),
        "uptime_hms": _format_hms(uptime_seconds),
    }
    stats["health"] = _health_score(stats)
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



def main() -> None:
    """Point d'entrée principal de l'agent."""
    parser = argparse.ArgumentParser(description="Agent de reporting fleet")
    parser.add_argument("--server", default="http://localhost:5000", help="URL du serveur (sans le chemin)")
    parser.add_argument("--path", default="/api/fleet/report", help="Chemin du endpoint")
    parser.add_argument("--interval", type=float, default=10.0, help="Intervalle en secondes")
    parser.add_argument("--token", default=os.environ.get("FLEET_TOKEN", ""), help="FLEET_TOKEN (sinon variable d'env)")
    parser.add_argument("--machine-id", default=get_machine_id(), help="Identifiant machine")
    args = parser.parse_args()

    if not args.token:
        print("Erreur: FLEET_TOKEN manquant (argument --token ou variable d'environnement)")
        raise SystemExit(1)

    url = args.server.rstrip("/") + args.path
    print(f"Agent démarré -> {url}")
    print(f"id={args.machine_id}, intervalle={args.interval}s")

    while True:
        report = collect_agent_stats()
        ok, msg = post_report(url, args.token, args.machine_id, report)
        status = "OK" if ok else "KO"
        short = f"CPU {report['cpu_percent']:.1f}% RAM {report['ram_percent']:.1f}% Disk {report['disk_percent']:.1f}%"
        if ok:
            print(f"[{time.strftime('%H:%M:%S')}] {status} {msg} | {short} | Score {report['health']['score']}/100")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {status} {msg} | ERREUR d'envoi | {short}")
        # Si le serveur est injoignable, on attend mais on ne quitte pas
        time.sleep(max(1.0, args.interval))


if __name__ == "__main__":
    main()
