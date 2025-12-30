"""Tableau de bord système : CPU, RAM, disque et uptime.
Fonctionne en mode CLI ou via une petite UI web Flask.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import threading
import tempfile
import time
import urllib.error
import urllib.request
import webbrowser
import zipfile
import uuid
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
ACTION_TOKEN = os.environ.get("ACTION_TOKEN")  # optionnel, protège les actions si défini
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # optionnel, webhook si santé critique
WEBHOOK_MIN_SECONDS = int(os.environ.get("WEBHOOK_MIN_SECONDS", "300"))
FLEET_TOKEN = os.environ.get("FLEET_TOKEN")  # token obligatoire pour les rapports agents
FLEET_TTL_SECONDS = int(os.environ.get("FLEET_TTL_SECONDS", "600"))  # expiration des entrées fleet
FLEET_STATE_PATH = Path("logs/fleet_state.json")

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


def _health_score(stats: Dict[str, object]) -> Dict[str, object]:
    """Calcule un score simple 0-100 et un statut (ok/warn/critical)."""

    def clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    cpu = float(stats["cpu_percent"])
    ram = float(stats["ram_percent"])
    disk = float(stats["disk_percent"])

    # Scores par composant (1 = parfait, 0 = mauvais)
    cpu_score = clamp(1 - max(0.0, (cpu - 50) / 50))  # plein à 50%, tombe à 0 à 100%
    ram_score = clamp(1 - max(0.0, (ram - 60) / 40))  # plein à 60%, tombe à 0 à 100%
    disk_score = clamp(1 - max(0.0, (disk - 70) / 30))  # plein à 70%, 0 à 100%

    # Pondérations simples
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


_LAST_WEBHOOK_TS = 0.0
FLEET_STATE: Dict[str, Dict[str, object]] = {}


def _load_fleet_state() -> None:
    """Recharge l'état fleet depuis le disque (best effort)."""
    global FLEET_STATE
    if not FLEET_STATE_PATH.exists():
        return
    try:
        data = json.loads(FLEET_STATE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            FLEET_STATE = {str(k): v for k, v in data.items()}
            # purge immédiate des entrées expirées si besoin
            now_ts = time.time()
            expired = [mid for mid, entry in FLEET_STATE.items() if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS]
            for mid in expired:
                FLEET_STATE.pop(mid, None)
            if expired:
                _save_fleet_state()
    except (OSError, json.JSONDecodeError):
        return


def _save_fleet_state() -> None:
    """Sauvegarde l'état fleet sur disque (best effort)."""
    try:
        FLEET_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FLEET_STATE_PATH.write_text(json.dumps(FLEET_STATE), encoding="utf-8")
    except OSError:
        return


_load_fleet_state()


def _disk_usage_target() -> str:
    """Choisit un point de montage qui fonctionne sous Windows et Unix."""
    home = Path.home()
    anchor = home.anchor or "/"
    return anchor


def _is_windows() -> bool:
    return os.name == "nt"


def _post_webhook(message: str) -> bool:
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
        with urllib.request.urlopen(req, timeout=5) as resp:  # pragma: no cover
            return 200 <= resp.getcode() < 300
    except urllib.error.URLError:
        return False


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


def _run_subprocess(cmd: list[str]) -> Dict[str, object]:
    """Exécute une commande et retourne ok/stdout/stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "ok": result.returncode == 0,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "code": result.returncode,
        }
    except Exception as exc:  # pragma: no cover - log brut
        return {"ok": False, "stdout": "", "stderr": str(exc), "code": -1}


def _action_flush_dns() -> Dict[str, object]:
    if not _is_windows():
        return {"ok": False, "message": "Action Windows uniquement"}
    return _run_subprocess(["ipconfig", "/flushdns"])


def _action_restart_spooler() -> Dict[str, object]:
    if not _is_windows():
        return {"ok": False, "message": "Action Windows uniquement"}
    return _run_subprocess(["powershell", "-Command", "Restart-Service -Name Spooler"])


def _action_cleanup_temp() -> Dict[str, object]:
    temp_dir = Path(tempfile.gettempdir())
    deleted = 0
    for path in temp_dir.glob("*.tmp"):
        try:
            path.unlink()
            deleted += 1
        except OSError:
            continue
    return {"ok": True, "message": f"Fichiers .tmp supprimés : {deleted}"}


def _action_cleanup_teams() -> Dict[str, object]:
    if not _is_windows():
        return {"ok": False, "message": "Action Windows uniquement"}
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Teams" / "Cache"
    if not base.exists():
        return {"ok": False, "message": "Cache Teams introuvable"}

    deleted = 0
    for path in base.rglob("*"):
        if path.is_file():
            try:
                path.unlink()
                deleted += 1
            except OSError:
                continue
    return {"ok": True, "message": f"Cache Teams vidé ({deleted} fichiers)"}


def _action_cleanup_outlook() -> Dict[str, object]:
    if not _is_windows():
        return {"ok": False, "message": "Action Windows uniquement"}
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Microsoft" / "Outlook"
    if not base.exists():
        return {"ok": False, "message": "Dossier Outlook introuvable"}

    deleted = 0
    for pattern in ("*.tmp", "*.dat"):
        for path in base.rglob(pattern):
            if path.is_file():
                try:
                    path.unlink()
                    deleted += 1
                except OSError:
                    continue
    return {"ok": True, "message": f"Caches Outlook nettoyés ({deleted} fichiers)"}


def _action_collect_logs() -> Dict[str, object]:
    temp_dir = Path(tempfile.gettempdir())
    zip_path = temp_dir / f"diag_logs_{int(time.time())}.zip"

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Stats courantes
            stats = collect_stats()
            zf.writestr("stats.json", json.dumps(stats, indent=2))

            # Historique CSV si présent
            if DEFAULT_HISTORY_CSV.exists():
                zf.write(DEFAULT_HISTORY_CSV, arcname="metrics.csv")

            # Réseau/OS minimal
            if _is_windows():
                net = _run_subprocess(["ipconfig", "/all"])
            else:
                net = _run_subprocess(["ifconfig"])
            zf.writestr("network.txt", net.get("stdout", ""))

        return {"ok": True, "message": f"Logs collectés : {zip_path}"}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "message": str(exc)}


def _maybe_send_webhook(stats: Dict[str, object]) -> None:
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
        f"Alerte santé critique: score={score}/100, "
        f"CPU={stats.get('cpu_percent', '?')}%, "
        f"RAM={stats.get('ram_percent', '?')}%, "
        f"Disk={stats.get('disk_percent', '?')}%"
    )
    sent = _post_webhook(msg)
    if sent:
        _LAST_WEBHOOK_TS = now


APPROVED_ACTIONS: Dict[str, object] = {
    "flush_dns": {
        "label": "Flush DNS",
        "runner": _action_flush_dns,
    },
    "restart_spooler": {
        "label": "Redémarrer Spooler",
        "runner": _action_restart_spooler,
    },
    "cleanup_temp": {
        "label": "Nettoyer Temp (*.tmp)",
        "runner": _action_cleanup_temp,
    },
    "cleanup_teams": {
        "label": "Nettoyer cache Teams",
        "runner": _action_cleanup_teams,
    },
    "cleanup_outlook": {
        "label": "Nettoyer caches Outlook",
        "runner": _action_cleanup_outlook,
    },
    "collect_logs": {
        "label": "Collecter logs (zip)",
        "runner": _action_collect_logs,
    },
}


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


@app.route("/fleet")
def fleet_page() -> str:
    # expose le TTL côté client pour cohérence (secondes)
    return render_template("fleet.html", fleet_ttl_seconds=FLEET_TTL_SECONDS)


@app.route("/api/stats")
def api_stats():
    return jsonify(collect_stats())


@app.route("/api/status")
def api_status():
    stats = collect_stats()
    stats["health"] = _health_score(stats)
    _maybe_send_webhook(stats)
    return jsonify(stats)


def _check_action_token() -> Dict[str, object] | None:
    if not ACTION_TOKEN:
        return {"error": "Token requis (définir ACTION_TOKEN)"}

    header = request.headers.get("Authorization", "")
    token = header.replace("Bearer", "").strip()
    if not token:
        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()
    if token != ACTION_TOKEN:
        return {"error": "Unauthorized"}
    return None


def _check_fleet_token() -> Dict[str, object] | None:
    if not FLEET_TOKEN:
        return {"error": "Token requis (définir FLEET_TOKEN)"}

    header = request.headers.get("Authorization", "")
    token = header.replace("Bearer", "").strip()
    if not token:
        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()
    if token != FLEET_TOKEN:
        return {"error": "Unauthorized"}
    return None


@app.route("/api/action", methods=["POST"])
def api_action():
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403

    payload = request.get_json(silent=True) or {}
    action_name = str(payload.get("action", "")).strip()
    if action_name not in APPROVED_ACTIONS:
        return jsonify({"error": "Action inconnue"}), 400

    runner = APPROVED_ACTIONS[action_name]["runner"]
    result = runner()
    return jsonify({"action": action_name, **result})


@app.route("/api/fleet/report", methods=["POST"])
def api_fleet_report():
    auth_err = _check_fleet_token()
    if auth_err:
        return jsonify(auth_err), 403

    payload = request.get_json(silent=True) or {}
    machine_id = str(payload.get("machine_id") or payload.get("id") or uuid.uuid4())
    if not machine_id:
        return jsonify({"error": "machine_id manquant"}), 400

    report = payload.get("report") or {}
    now_ts = time.time()

    FLEET_STATE[machine_id] = {
        "id": machine_id,
        "report": report,
        "ts": now_ts,
        "client": request.remote_addr,
    }

    _save_fleet_state()

    return jsonify({"ok": True})


@app.route("/api/fleet")
def api_fleet():
    # purge les entrées expirées
    now_ts = time.time()
    expired = []
    for mid, entry in list(FLEET_STATE.items()):
        if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS:
            expired.append(mid)
            FLEET_STATE.pop(mid, None)

    if expired:
        _save_fleet_state()

    data = list(FLEET_STATE.values())
    return jsonify({"count": len(data), "expired": expired, "data": data})


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
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Hôte Flask quand --web est activé")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")), help="Port Flask quand --web est activé")
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
