# ALWAYS keep this import as the very first line:

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
import hmac
from pathlib import Path
from typing import Dict, Iterable

import psutil
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from marshmallow import Schema, fields, ValidationError

from db_utils import insert_fleet_report
from fleet_utils import format_bytes_to_gib, format_uptime_hms, calculate_health_score
from constants import (
    CPU_ALERT, RAM_ALERT, FLEET_TTL_SECONDS as DEFAULT_FLEET_TTL,
    WEBHOOK_MIN_SECONDS as DEFAULT_WEBHOOK_MIN_SECONDS,
    SESSION_TIMEOUT as DEFAULT_SESSION_TIMEOUT
)
from logging_config import setup_logging


app = Flask(__name__, template_folder="templates", static_folder="static")

_secret = os.environ.get('SECRET_KEY')
if not _secret and os.environ.get('ALLOW_DEV_INSECURE') == '1':
    _secret = 'dev-secret-key'
if not _secret:
    raise RuntimeError("SECRET_KEY manquant : définissez-le ou ALLOW_DEV_INSECURE=1 pour un dev local.")
app.secret_key = _secret

swagger = Swagger(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],
    storage_uri=os.environ.get("FLASK_LIMITER_STORAGE_URI", "memory://"),
)


# --- Route temporaire de debug pour lister les templates ---
# ATTENTION : À désactiver en production !
@app.route('/debug-templates')
def debug_templates():
    if os.environ.get('ENABLE_DEBUG_TEMPLATES') != '1':
        return "Not found", 404
    # TODO: restreindre l'accès à cette route (admin uniquement)
    import os
    template_dir = app.template_folder or 'templates'
    try:
        files = os.listdir(template_dir)
        return '<br>'.join(files)
    except Exception as e:
        return f"Erreur accès dossier templates : {e}", 500


# --- Initialisation du compte admin (une seule fois) ---
def create_admin_table():
    conn = sqlite3.connect(str(FLEET_DB_PATH))
    conn.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()


def ensure_bootstrap_admin():
    """Crée ou met à jour un admin via variables d'env si activé.

    - ADMIN_BOOTSTRAP_USERNAME / ADMIN_BOOTSTRAP_PASSWORD doivent être définies.
    - Si aucun admin n'existe : création.
    - Si ADMIN_FORCE_BOOTSTRAP=1 et qu'un admin existe : met à jour le premier admin (reset user/mot de passe).
    """
    user = os.environ.get("ADMIN_BOOTSTRAP_USERNAME")
    pwd = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD")
    if not user or not pwd:
        return
    force = os.environ.get("ADMIN_FORCE_BOOTSTRAP") == "1"
    create_admin_table()
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.execute('SELECT id, COUNT(*) OVER() as c FROM admin ORDER BY id ASC LIMIT 1')
        row = cur.fetchone()
        if not row or row[1] == 0:
            from werkzeug.security import generate_password_hash
            conn.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', (user, generate_password_hash(pwd)))
            conn.commit()
            logging.info("Admin bootstrap créé via variables d'environnement.")
        elif force:
            from werkzeug.security import generate_password_hash
            first_id = row[0]
            conn.execute('UPDATE admin SET username = ?, password_hash = ? WHERE id = ?', (user, generate_password_hash(pwd), first_id))
            conn.commit()
            logging.info("Admin bootstrap forcé : compte mis à jour via variables d'environnement.")
    except Exception as e:
        logging.error(f"Erreur bootstrap admin : {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.route('/init-admin', methods=['GET', 'POST'])
def init_admin():
    create_admin_table()
    conn = sqlite3.connect(str(FLEET_DB_PATH))
    cur = conn.execute('SELECT COUNT(*) FROM admin')
    if cur.fetchone()[0] > 0:
        conn.close()
        return 'Admin déjà initialisé.'
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        from werkzeug.security import generate_password_hash
        hash_pw = generate_password_hash(password)
        try:
            conn.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', (username, hash_pw))
            conn.commit()
            flash('Admin créé. Connectez-vous.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Erreur : ' + str(e))
    conn.close()
    return render_template('init_admin.html')


# --- Authentification minimale par mot de passe unique ---
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("DASHBOARD_CONFIG") or (BASE_DIR / "config.json"))


def _get_dashboard_password() -> str | None:
    env_pwd = os.environ.get("DASHBOARD_PASSWORD")
    if env_pwd:
        return str(env_pwd)
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            pwd = data.get("dashboard_password")
            if pwd:
                return str(pwd)
    except Exception as e:
        logging.error(f"Erreur lecture config.json pour dashboard_password : {e}")
    return None


def require_password(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("pw_ok"):
            return view_func(*args, **kwargs)
        nxt = request.path
        return redirect(url_for("login", next=nxt))
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    expected = _get_dashboard_password()
    if not expected:
        flash("Mot de passe non configuré (config.json -> dashboard_password ou env DASHBOARD_PASSWORD)")
    if request.method == 'POST':
        password = request.form.get('password', '')
        next_url = request.args.get('next') or url_for('dashboard')
        if expected and hmac.compare_digest(password, expected):
            session.clear()
            session['pw_ok'] = True
            session.permanent = True
            return redirect(next_url)
        flash('Mot de passe invalide')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Schéma Marshmallow pour la validation avancée du rapport agent


class ReportSchema(Schema):
    machine_id = fields.Str(required=True)
    report = fields.Dict(required=True)



class MetricsSchema(Schema):
    cpu_percent = fields.Float(required=True)
    ram_percent = fields.Float(required=True)
    disk_percent = fields.Float(required=True)
    timestamp = fields.Str(required=False)
    ram_used_gib = fields.Float(required=False)
    ram_total_gib = fields.Float(required=False)
    disk_used_gib = fields.Float(required=False)
    disk_total_gib = fields.Float(required=False)
    uptime_seconds = fields.Float(required=False)
    uptime_hms = fields.Str(required=False)
    health = fields.Dict(required=False)



report_schema = ReportSchema()
metrics_schema = MetricsSchema()
"""Tableau de bord système : CPU, RAM, disque et uptime.
Fonctionne en mode CLI ou via une petite UI web Flask.
"""

import argparse

# Journalisation dans un fichier log
# Initialize logging using centralized configuration
setup_logging()

# CPU_ALERT = 80.0  # importé de constants.py
# RAM_ALERT = 90.0  # importé de constants.py

DEFAULT_HISTORY_CSV = Path("logs/metrics.csv")
DEFAULT_EXPORT_CSV = Path.home() / "Desktop" / "metrics.csv"
DEFAULT_EXPORT_JSONL = Path.home() / "Desktop" / "metrics.jsonl"
ACTION_TOKEN = os.environ.get("ACTION_TOKEN")  # optionnel, protège les actions si défini
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # optionnel, webhook si santé critique
WEBHOOK_MIN_SECONDS = int(os.environ.get("WEBHOOK_MIN_SECONDS", str(DEFAULT_WEBHOOK_MIN_SECONDS)))
FLEET_TOKEN = os.environ.get("FLEET_TOKEN")  # token obligatoire pour les rapports agents
FLEET_TTL_SECONDS = int(os.environ.get("FLEET_TTL_SECONDS", str(DEFAULT_FLEET_TTL)))
FLEET_STATE_PATH = Path("logs/fleet_state.json")
FLEET_DB_PATH = Path("data/fleet.db")
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(DEFAULT_SESSION_TIMEOUT)))

# Crée automatiquement un admin si la table est vide et que les variables d'env sont présentes.
ensure_bootstrap_admin()

# DB schema notes:
# - organizations(id TEXT PRIMARY KEY, name TEXT)
# - api_keys(key TEXT PRIMARY KEY, org_id TEXT, created_at REAL, revoked INTEGER)
# - fleet(id TEXT PRIMARY KEY, report TEXT, ts REAL, client TEXT, org_id TEXT)

# Force la migration de la base au démarrage

def _detect_alerts(cpu_percent: float, ram_percent: float) -> Dict[str, bool]:
    return {
        "cpu": cpu_percent >= CPU_ALERT,
        "ram": ram_percent >= RAM_ALERT,
    }


_LAST_WEBHOOK_TS = 0.0
FLEET_STATE: Dict[str, Dict[str, object]] = {}
def _load_fleet_state() -> None:
    """Recharge l'état fleet depuis la base SQLite si présente, sinon depuis le JSON (best effort)."""
    global FLEET_STATE
    # Automatic migration/merge: if JSON backup exists, import or merge into SQLite
    try:
        if FLEET_STATE_PATH.exists():
            try:
                if not FLEET_DB_PATH.exists():
                    # create DB and import JSON entries
                    conn = sqlite3.connect(str(FLEET_DB_PATH))
                    cur = conn.cursor()
                    cur.execute('CREATE TABLE IF NOT EXISTS fleet (id TEXT PRIMARY KEY, report TEXT, ts REAL, client TEXT)')
                    raw = FLEET_STATE_PATH.read_text(encoding='utf-8') or '{}'
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        for mid, entry in data.items():
                            report_json = json.dumps(entry.get('report', {}), ensure_ascii=False)
                            ts = entry.get('ts', time.time())
                            client = entry.get('client')
                            sql = (
                                'INSERT OR REPLACE INTO fleet (id, report, ts, client) '
                                'VALUES (?, ?, ?, ?)'
                            )
                            params = (str(mid), report_json, ts, client)
                            cur.execute(sql, params)
                    conn.commit()
                    conn.close()
                else:
                    # merge newer entries from JSON into existing DB
                    try:
                        raw = FLEET_STATE_PATH.read_text(encoding='utf-8') or '{}'
                        data = json.loads(raw)
                        if isinstance(data, dict):
                            conn = sqlite3.connect(str(FLEET_DB_PATH))
                            cur = conn.cursor()
                            for mid, entry in data.items():
                                ts = entry.get('ts', 0)
                                cur.execute('SELECT ts FROM fleet WHERE id = ?', (mid,))
                                row = cur.fetchone()
                                if not row or ts > (row[0] or 0):
                                    report_json = json.dumps(entry.get('report', {}), ensure_ascii=False)
                                    client = entry.get('client')
                                    sql = (
                                        'INSERT OR REPLACE INTO fleet (id, report, ts, client) '
                                        'VALUES (?, ?, ?, ?)'
                                    )
                                    params = (str(mid), report_json, ts, client)
                                    cur.execute(sql, params)
                            conn.commit()
                            conn.close()
                    except Exception as e:
                        logging.error(f"Erreur lors de la fusion JSON->DB fleet : {e}")
            except Exception as e:
                logging.error(f"Erreur migration JSON->DB fleet : {e}")
    except Exception as e:
        logging.error(f"Erreur lors du chargement de l'état fleet : {e}")

    # prefer DB if present
    try:
        if FLEET_DB_PATH.exists():
            conn = sqlite3.connect(str(FLEET_DB_PATH))
            cur = conn.cursor()
            cur.execute("SELECT id, report, ts, client, org_id FROM fleet")
            rows = cur.fetchall()
            conn.close()
            FLEET_STATE = {}
            for rid, report_json, ts, client, org_id in rows:
                try:
                    report = json.loads(report_json) if report_json else {}
                except Exception:
                    report = {}
                # keep org_id per entry for filtering
                FLEET_STATE[str(rid)] = {
                    "id": str(rid),
                    "report": report,
                    "ts": ts or 0,
                    "client": client,
                    "org_id": org_id,
                }
            # purge expirés
            now_ts = time.time()
            expired = [mid for mid, entry in FLEET_STATE.items() if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS]
            for mid in expired:
                FLEET_STATE.pop(mid, None)
            if expired:
                _save_fleet_state()
            return
    except Exception:
        # fall back to JSON
        pass

    # fallback JSON file
    if not FLEET_STATE_PATH.exists():
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
        return


def _save_fleet_state() -> None:
    """Sauvegarde l'état fleet en base SQLite (préféré) et en JSON backup (best effort)."""
    try:
        # ensure folder for json backup
        FLEET_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # write JSON backup (legacy flat mapping by machine_id for compatibility)
        try:
            flat: dict = {}
            for k, v in FLEET_STATE.items():
                mid = v.get('id') or k
                flat[str(mid)] = v
            FLEET_STATE_PATH.write_text(json.dumps(flat), encoding="utf-8")
        except OSError as e:
            logging.error(f"Erreur sauvegarde JSON fleet : {e}")

        # ensure db dir and table
        try:
            FLEET_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(FLEET_DB_PATH))
            cur = conn.cursor()
            cur.execute(
                'CREATE TABLE IF NOT EXISTS fleet (id TEXT PRIMARY KEY, report TEXT, ts REAL, client TEXT, org_id TEXT)'
            )
            # upsert all entries (id stored must be unique, include org if needed)
            for mid, entry in FLEET_STATE.items():
                report_json = json.dumps(entry.get('report', {}), ensure_ascii=False)
                ts = entry.get('ts', time.time())
                client = entry.get('client')
                org_id = entry.get('org_id')
                cur.execute(
                    'INSERT OR REPLACE INTO fleet (id, report, ts, client, org_id) VALUES (?, ?, ?, ?, ?)',
                    (str(mid), report_json, ts, client, org_id),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Erreur sauvegarde DB fleet : {e}")
    except Exception as e:
        logging.error(f"Erreur générale sauvegarde fleet : {e}")
        return


# DB/backup loading will be initialized when the application starts (see main())


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


def _action_sync_time() -> Dict[str, object]:
    """Synchronize system time with NTP server."""
    if _is_windows():
        return _run_subprocess(["powershell", "-Command", "net start w32time; w32tm /resync"])
    else:
        result = _run_subprocess(["timedatectl", "set-ntp", "true"])
        if not result.get("ok"):
            result = _run_subprocess(["ntpdate", "-s", "pool.ntp.org"])
        return result


def _action_restart_network() -> Dict[str, object]:
    """Restart network adapter(s)."""
    if _is_windows():
        return _run_subprocess(["powershell", "-Command", "ipconfig /release; ipconfig /renew"])
    else:
        return _run_subprocess(["sudo", "systemctl", "restart", "networking"])


def _action_clear_recyclebin() -> Dict[str, object]:
    """Empty recycle bin (Windows only)."""
    if not _is_windows():
        return {"ok": False, "message": "Action Windows uniquement"}
    return _run_subprocess(["powershell", "-Command", "Clear-RecycleBin -Force -Confirm:$false"])


def _action_clear_event_logs() -> Dict[str, object]:
    """Clear Windows Event Logs (Windows only)."""
    if not _is_windows():
        return {"ok": False, "message": "Action Windows uniquement"}
    result = _run_subprocess(["powershell", "-Command",
        "Clear-EventLog -LogName Application,System -Confirm:$false"])
    return result


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


def _ensure_db_schema() -> None:
    try:
        FLEET_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        # organizations table (ajout du champ role)
        cur.execute(
            'CREATE TABLE IF NOT EXISTS organizations (id TEXT PRIMARY KEY, name TEXT, role TEXT DEFAULT "user")'
        )
        # migration si la colonne role n'existe pas encore
        try:
            cur.execute('ALTER TABLE organizations ADD COLUMN role TEXT DEFAULT "user"')
        except Exception as e:
            logging.info(f"Colonne role déjà existante ou erreur : {e}")
        # api_keys table
        cur.execute(
            'CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY, org_id TEXT, created_at REAL, revoked INTEGER DEFAULT 0)'
        )
        # fleet table (may already exist without org_id)
        cur.execute(
            'CREATE TABLE IF NOT EXISTS fleet (id TEXT PRIMARY KEY, report TEXT, ts REAL, client TEXT, org_id TEXT)'
        )
        # sessions table for server-side session exchange (sid -> org_id)
        cur.execute(
            'CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, org_id TEXT, created_at REAL, expires_at REAL)'
        )
        # download tokens for agent installer links (token -> path/expires/used)
        cur.execute(
            'CREATE TABLE IF NOT EXISTS download_tokens (token TEXT PRIMARY KEY, path TEXT, created_at REAL, expires_at REAL, used INTEGER DEFAULT 0)'
        )
        # attempt to add org_id column if missing (sqlite ignores if exists on many versions, so safe)
        try:
            cur.execute('ALTER TABLE fleet ADD COLUMN org_id TEXT')
        except Exception as e:
            logging.info(f"Colonne org_id déjà existante ou erreur : {e}")
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors de la création du schéma DB : {e}")
        return
        


def _create_default_org_from_env() -> None:
    """If FLEET_TOKEN env is present, ensure a default organization exists mapped to that key."""
    if not FLEET_TOKEN:
        return
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        # create a deterministic org id for legacy token
        org_id = "org_default"
        cur.execute('INSERT OR IGNORE INTO organizations (id, name) VALUES (?, ?)', (org_id, 'default'))
        # insert api_key mapping
        cur.execute('INSERT OR IGNORE INTO api_keys (key, org_id, created_at, revoked) VALUES (?, ?, ?, 0)',
                    (FLEET_TOKEN, org_id, time.time()))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur création org par défaut : {e}")
        return


def _get_org_for_key(key: str) -> str | None:
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('SELECT org_id, revoked FROM api_keys WHERE key = ?', (key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        org_id, revoked = row
        if revoked:
            return None
        return org_id
    except Exception as e:
        logging.error(f"Erreur récupération org pour clé : {e}")
        return None


def _get_org_for_session(sid: str) -> str | None:
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('SELECT org_id, expires_at FROM sessions WHERE id = ?', (sid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        org_id, expires_at = row
        if expires_at and time.time() > (expires_at or 0):
            # expired
            try:
                conn = sqlite3.connect(str(FLEET_DB_PATH))
                cur = conn.cursor()
                cur.execute('DELETE FROM sessions WHERE id = ?', (sid,))
                conn.commit()
                conn.close()
            except Exception as e:
                logging.error(f"Erreur suppression session expirée : {e}")
            return None
        return org_id
    except Exception as e:
        logging.error(f"Erreur récupération org pour session : {e}")
        return None


def _check_org_key() -> tuple[bool, str | None]:
    """Returns (ok, org_id) where ok False means unauthorized.
    Accepts Authorization header or token in JSON payload (backwards-compatible).
    """
    header = request.headers.get("Authorization", "")
    token = header.replace("Bearer", "").strip()
    if not token:
        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()
    if not token:
        # fallback: check for server-side session cookie
        sid = request.cookies.get('dashfleet_sid')
        if sid:
            org = _get_org_for_session(sid)
            if org:
                return True, org
        return False, None
    org_id = _get_org_for_key(token)
    if org_id:
        return True, org_id
    return False, None


APPROVED_ACTIONS: Dict[str, object] = {
    "sync_time": {
        "label": "Synchroniser l'heure",
        "runner": _action_sync_time,
    },
    "flush_dns": {
        "label": "Vider cache DNS",
        "runner": _action_flush_dns,
    },
    "restart_network": {
        "label": "Redémarrer réseau",
        "runner": _action_restart_network,
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
    "clear_recyclebin": {
        "label": "Vider Corbeille",
        "runner": _action_clear_recyclebin,
    },
    "clear_event_logs": {
        "label": "Effacer Event Logs",
        "runner": _action_clear_event_logs,
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
@require_password
def dashboard() -> str:
    return render_template("index.html")


@app.route("/history")
@require_password
def history_page() -> str:
    return render_template("history.html")


@app.route("/fleet")
def fleet_page() -> str:
    # Page simple sans authentification
    return render_template("fleet.html")


@app.route("/help")
@require_password
def help_page() -> str:
    return render_template("help.html")


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


def _create_download_token(file_path: str, ttl_seconds: int = 3600) -> str | None:
    try:
        token = secrets.token_urlsafe(24)
        now = time.time()
        expires = now + int(ttl_seconds)
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('INSERT INTO download_tokens (token, path, created_at, expires_at, used) VALUES (?, ?, ?, ?, 0)',
                    (token, str(file_path), now, expires))
        conn.commit()
        conn.close()
        return token
    except Exception as e:
        logging.error(f"Erreur création download token : {e}")
        return None


def _consume_download_token(token: str) -> str | None:
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('SELECT path, expires_at, used FROM download_tokens WHERE token = ?', (token,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        path, expires_at, used = row
        if used:
            conn.close()
            return None
        if expires_at and time.time() > (expires_at or 0):
            # expired
            try:
                cur.execute('DELETE FROM download_tokens WHERE token = ?', (token,))
                conn.commit()
            except Exception as e:
                logging.error(f"Erreur suppression token expiré : {e}")
            conn.close()
            return None
        # mark used
        try:
            cur.execute('UPDATE download_tokens SET used = 1 WHERE token = ?', (token,))
            conn.commit()
        except Exception as e:
            logging.error(f"Erreur update token utilisé : {e}")
        conn.close()
        return path
    except Exception as e:
        logging.error(f"Erreur consommation download token : {e}")
        return None


@app.route("/api/orgs", methods=["POST"])
@limiter.limit("10/minute")
def api_create_org():
    """Créer une organization + api_key. Protégé par ACTION_TOKEN. Le premier org devient admin, les suivants user."""
    auth_err = _check_action_token()
    if auth_err:
        logging.warning(f"Accès refusé /api/orgs depuis {request.remote_addr}")
        return jsonify(auth_err), 403

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        logging.error(f"JSON invalide /api/orgs : {e}")
        return jsonify({"error": "JSON invalide"}), 400
    name = str(payload.get("name") or "").strip()
    if not name or len(name) < 3:
        logging.error(f"Nom organisation trop court /api/orgs : {name}")
        return jsonify({"error": "name requis (min 3 caractères)"}), 400

    # Déterminer le rôle : admin si première org, sinon user
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM organizations')
        count = cur.fetchone()[0]
        role = "admin" if count == 0 else "user"
        conn.close()
    except Exception:
        role = "user"

    org_id = f"org_{secrets.token_hex(6)}"
    key = secrets.token_hex(16)
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('INSERT INTO organizations (id, name, role) VALUES (?, ?, ?)', (org_id, name, role))
        cur.execute('INSERT INTO api_keys (key, org_id, created_at, revoked) VALUES (?, ?, ?, 0)', (key, org_id, time.time()))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur DB /api/orgs : insertion échouée : {e}")
        return jsonify({"error": "db error"}), 500
    user_agent = request.headers.get("User-Agent", "")
    logging.info(f"user_agent={user_agent}")
    logging.info(f"Organisation créée : {org_id} ({name}) role={role}")
    return jsonify({"org_id": org_id, "api_key": key, "name": name, "role": role})


@app.route("/api/login", methods=["POST"])
def api_login():
    """Exchange an API key for a short-lived server-side session cookie."""
    payload = request.get_json(silent=True) or {}
    key = str(payload.get("api_key") or payload.get("key") or "").strip()
    if not key:
        return jsonify({"error": "api_key requis"}), 400
    org = _get_org_for_key(key)
    if not org:
        return jsonify({"error": "Unauthorized"}), 403

    sid = secrets.token_urlsafe(24)
    now = time.time()
    expires = now + SESSION_TTL_SECONDS
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        sql = (
            'INSERT INTO sessions (id, org_id, created_at, expires_at) '
            'VALUES (?, ?, ?, ?)'
        )
        cur.execute(sql, (sid, org, now, expires))
        conn.commit()
        conn.close()
    except Exception:
        return jsonify({"error": "db error"}), 500

    resp = jsonify({"ok": True, "expires_in": SESSION_TTL_SECONDS})
    resp.set_cookie(
        'dashfleet_sid',
        sid,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite='Lax',
        path='/'
    )
    return resp


@app.route("/api/logout", methods=["POST"])
def api_logout():
    sid = request.cookies.get('dashfleet_sid')
    if sid:
        try:
            conn = sqlite3.connect(str(FLEET_DB_PATH))
            cur = conn.cursor()
            cur.execute('DELETE FROM sessions WHERE id = ?', (sid,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    resp = jsonify({"ok": True})
    resp.set_cookie('dashfleet_sid', '', expires=0, path='/')
    return resp


@app.route("/api/orgs", methods=["GET"])
def api_list_orgs():
    """Liste des organisations et clés (protégé par ACTION_TOKEN)."""
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403

    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('SELECT id, name FROM organizations')
        orgs = cur.fetchall()
        result = []
        for oid, name in orgs:
            cur.execute('SELECT key, created_at, revoked FROM api_keys WHERE org_id = ?', (oid,))
            keys = cur.fetchall()
            key_list = []
            for k, created_at, revoked in keys:
                masked = (k[:6] + '...' + k[-4:]) if k else None
                key_list.append({"key_masked": masked, "created_at": created_at, "revoked": bool(revoked)})
            result.append({"org_id": oid, "name": name, "keys": key_list})
        conn.close()
        return jsonify({"count": len(result), "orgs": result})
    except Exception:
        return jsonify({"error": "db error"}), 500


@app.route("/api/keys/revoke", methods=["POST"])
def api_revoke_key():
    """Révoque ou restaure une clé API (protégé par ACTION_TOKEN)."""
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403

    payload = request.get_json(silent=True) or {}
    key = str(payload.get("key") or "").strip()
    revoke = bool(payload.get("revoke", True))
    if not key:
        return jsonify({"error": "key requis"}), 400

    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('UPDATE api_keys SET revoked = ? WHERE key = ?', (1 if revoke else 0, key))
        conn.commit()
        changed = cur.rowcount
        conn.close()
        if changed:
            return jsonify({"ok": True, "revoked": revoke})
        return jsonify({"ok": False, "message": "clé inconnue"}), 404
    except Exception:
        return jsonify({"error": "db error"}), 500




@app.route("/admin/orgs")
@require_password
def admin_orgs():
    return render_template("admin_orgs.html")

@app.route("/admin/tokens")
@require_password
def admin_tokens():
    return render_template("admin_tokens.html")


@app.route('/api/tokens', methods=['GET'])
def api_list_tokens():
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('SELECT token, path, created_at, expires_at, used FROM download_tokens ORDER BY created_at DESC')
        rows = cur.fetchall()
        conn.close()
        items = []
        for token, path, created_at, expires_at, used in rows:
            items.append({
                'token_masked': token[:6] + '...' + token[-4:],
                'token': token,
                'path': path,
                'created_at': created_at,
                'expires_at': expires_at,
                'used': bool(used),
            })
        return jsonify({'count': len(items), 'items': items})
    except Exception:
        return jsonify({'error': 'db error'}), 500


@app.route('/api/tokens/create', methods=['POST'])
def api_create_token():
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403
    payload = request.get_json(silent=True) or {}
    path = payload.get('path') or str(Path('dist') / 'fleet_agent.exe')
    ttl = int(payload.get('ttl', 3600))
    if not Path(path).exists():
        return jsonify({'error': 'file not found', 'path': path}), 404
    token = _create_download_token(path, ttl_seconds=ttl)
    if not token:
        return jsonify({'error': 'could not create token'}), 500
    return jsonify({'ok': True, 'token': token, 'link': f'/download/agent/{token}', 'expires_in': ttl})


@app.route('/api/tokens/delete', methods=['POST'])
def api_delete_token():
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403
    payload = request.get_json(silent=True) or {}
    token = str(payload.get('token') or '').strip()
    if not token:
        return jsonify({'error': 'token required'}), 400
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        cur.execute('DELETE FROM download_tokens WHERE token = ?', (token,))
        changed = cur.rowcount
        conn.commit()
        conn.close()
        if changed:
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'message': 'token not found'}), 404
    except Exception:
        return jsonify({'error': 'db error'}), 500


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
@limiter.limit("10/minute")
def api_action():
    auth_err = _check_action_token()
    if auth_err:
        logging.warning(f"Accès refusé /api/action depuis {request.remote_addr}")
        return jsonify(auth_err), 403

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        logging.error(f"JSON invalide /api/action : {e}")
        return jsonify({"error": "JSON invalide"}), 400

    action_name = str(payload.get("action", "")).strip()
    if action_name not in APPROVED_ACTIONS:
        logging.error(f"Action inconnue /api/action : {action_name}")
        return jsonify({"error": "Action inconnue"}), 400

    runner = APPROVED_ACTIONS[action_name]["runner"]
    try:
        result = runner()
    except Exception as e:
        logging.error(f"Erreur exécution action {action_name} : {e}")
        return jsonify({"error": f"Erreur action {action_name}"}), 500
    user_agent = request.headers.get("User-Agent", "")
    # org_id n'est pas défini ici, donc on ne le log pas
    logging.info(f"user_agent={user_agent}")
    logging.info(f"Action exécutée : {action_name} par {request.remote_addr}")
    return jsonify({"action": action_name, **result})


@app.route("/api/agent/link", methods=["POST"])
def api_create_agent_link():
    """Create a one-time download token for the agent executable. Protected by ACTION_TOKEN."""
    auth_err = _check_action_token()
    if auth_err:
        return jsonify(auth_err), 403

    payload = request.get_json(silent=True) or {}
    ttl = int(payload.get('ttl', 3600))
    # default to dist/fleet_agent.exe
    agent_path = payload.get('path') or str(Path('dist') / 'fleet_agent.exe')
    if not Path(agent_path).exists():
        return jsonify({'error': 'Agent file not found', 'path': agent_path}), 404

    token = _create_download_token(agent_path, ttl_seconds=ttl)
    if not token:
        return jsonify({'error': 'could not create token'}), 500

    link = f"/download/agent/{token}"
    return jsonify({'ok': True, 'link': link, 'expires_in': ttl})


@app.route('/download/agent/<token>')
def download_agent(token: str):
    # allow either ACTION_TOKEN in header or a one-time token path
    # first attempt to consume the token
    path = _consume_download_token(token)
    if path:
        try:
            return app.send_static_file(os.path.relpath(path, start='static') )
        except Exception:
            # fallback: use flask send_file
            from flask import send_file
            try:
                return send_file(path, as_attachment=True)
            except Exception:
                return jsonify({'error': 'file not available'}), 404

    # else check ACTION_TOKEN header and allow direct download if provided
    header = request.headers.get('Authorization', '')
    token_hdr = header.replace('Bearer', '').strip()
    if token_hdr and token_hdr == ACTION_TOKEN:
        # serve default dist file
        agent = Path('dist') / 'fleet_agent.exe'
        if agent.exists():
            from flask import send_file
            return send_file(str(agent), as_attachment=True)
    return jsonify({'error': 'Unauthorized or invalid token'}), 403


@app.route("/api/fleet/report", methods=["POST"])
@limiter.limit("30/minute")
def api_fleet_report():
    """
    Reporte les métriques d'un agent.
    ---
    tags:
        - Fleet
    parameters:
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
                machine_id:
                    type: string
                report:
                    type: object
                    properties:
                        cpu_percent:
                            type: number
                        ram_percent:
                            type: number
                        disk_percent:
                            type: number
    responses:
        200:
            description: Rapport accepté
        400:
            description: Erreur de validation
        403:
            description: Non autorisé
    """
    ok, org_id = _check_org_key()
    if not ok or not org_id:
        logging.warning(f"Accès refusé /api/fleet/report depuis {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        payload = request.get_json(force=True)
        # Validation avancée du schéma principal
        data = report_schema.load(payload)
        # Validation avancée des métriques
        metrics_schema.load(data['report'])
    except ValidationError as ve:
        logging.error(f"Validation Marshmallow /api/fleet/report : {ve.messages}")
        return jsonify({"error": ve.messages}), 400
    except Exception as e:
        logging.error(f"JSON invalide /api/fleet/report : {e}")
        return jsonify({"error": "JSON invalide"}), 400

    machine_id = data['machine_id']
    report = data['report']
    now_ts = time.time()
    store_key = f"{org_id}:{machine_id}"
    insert_fleet_report(store_key, machine_id, report, now_ts, request.remote_addr, org_id, FLEET_STATE, _save_fleet_state)
    user_agent = request.headers.get("User-Agent", "")
    logging.info(f"org_id={org_id} user_agent={user_agent}")
    logging.info(f"Report reçu pour {machine_id} ({org_id}) de {request.remote_addr}")
    return jsonify({"ok": True})


@app.route("/api/fleet")
def api_fleet():
    # require org-key to list fleet (multi-tenant)
    ok, org_id = _check_org_key()
    if not ok or not org_id:
        return jsonify({"error": "Unauthorized"}), 403

    # purge entries expired for this org
    now_ts = time.time()
    expired = []
    for mid, entry in list(FLEET_STATE.items()):
        if entry.get("org_id") != org_id:
            continue
        if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS:
            expired.append(entry.get("id") or mid)
            FLEET_STATE.pop(mid, None)

    if expired:
        _save_fleet_state()

    data = [v for v in FLEET_STATE.values() if v.get("org_id") == org_id]
    return jsonify({"count": len(data), "expired": expired, "data": data})


@app.route("/api/fleet/public")
def api_fleet_public():
    # Public version: return all machines (no auth required)
    now_ts = time.time()
    expired = []
    for mid, entry in list(FLEET_STATE.items()):
        if now_ts - entry.get("ts", 0) > FLEET_TTL_SECONDS:
            expired.append(entry.get("id") or mid)
            FLEET_STATE.pop(mid, None)

    if expired:
        _save_fleet_state()

    data = list(FLEET_STATE.values())
    return jsonify({"count": len(data), "expired": expired, "data": data})


@app.route("/api/fleet/reload", methods=["POST"])
def api_fleet_reload():
    """Forcer le rechargement de `logs/fleet_state.json` en mémoire.

    Protégé par `FLEET_TOKEN` pour éviter les usages non autorisés.
    """
    ok, org_id = _check_org_key()
    if not ok or not org_id:
        return jsonify({"error": "Unauthorized"}), 403

    # reload global state from DB/JSON, but report back filtered count
    _load_fleet_state()
    count = sum(1 for v in FLEET_STATE.values() if v.get("org_id") == org_id)
    return jsonify({"ok": True, "count": count})


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
    import requests
    print("Surveillance en cours. Ctrl+C pour arrêter. \n")
    args = parse_args()
    server_url = getattr(args, 'server', "http://127.0.0.1:5000")
    api_key = os.environ.get("FLEET_API_KEY")
    try:
        while True:
            stats = collect_stats()
            print_stats(stats)

            # Envoi au serveur distant si api_key et server_url sont définis
            if api_key and server_url:
                try:
                    resp = requests.post(
                        f"{server_url.rstrip('/')}/api/fleet/report",
                        json={"report": stats},
                        headers={"Authorization": f"Bearer {api_key}"},
                        timeout=10
                    )
                    if resp.status_code != 200:
                        print(f"[WARN] Report POST failed: {resp.status_code} {resp.text}")
                except Exception as e:
                    print(f"[ERROR] Report POST exception: {e}")

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


def start_session_cleaner(interval: int = 60) -> None:
    """Démarre un thread qui purge régulièrement les sessions expirées de la DB."""

    def _loop() -> None:
        while True:
            try:
                conn = sqlite3.connect(str(FLEET_DB_PATH))
                cur = conn.cursor()
                now = time.time()
                cur.execute('DELETE FROM sessions WHERE expires_at IS NOT NULL AND expires_at < ?', (now,))
                conn.commit()
                conn.close()
            except Exception as e:
                logging.error(f"Erreur purge sessions expirées : {e}")
            time.sleep(interval)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tableau de bord système : CLI et UI Flask")
    parser.add_argument(
        "--server",
        type=str,
        default=os.environ.get("FLEET_SERVER", "http://127.0.0.1:5000"),
        help="URL du serveur DashFleet pour l'agent (ex: https://www.dash-fleet.com)"
    )
    parser.add_argument("--web", action="store_true", help="Lancer l’UI web Flask au lieu de la sortie CLI")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Hôte Flask quand --web est activé")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")), help="Port Flask quand --web est activé")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalle de rafraîchissement en secondes pour le mode CLI")
    parser.add_argument(
        "--export-csv",
        type=Path,
        default=DEFAULT_EXPORT_CSV,
        help=(
            "Chemin CSV pour enregistrer les mesures (défaut: "
            "Bureau/metrics.csv)"
        ),
    )
    parser.add_argument(
        "--export-jsonl",
        type=Path,
        default=DEFAULT_EXPORT_JSONL,
        help=(
            "Chemin JSONL pour enregistrer les mesures (défaut: "
            "Bureau/metrics.jsonl)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Ensure DB schema and migrate JSON backup -> SQLite if needed before running
    _ensure_db_schema()
    _create_default_org_from_env()
    _load_fleet_state()
    # Si lancé par double-clic sans arguments, on bascule en mode web par défaut.
    if len(sys.argv) == 1:
        args.web = True

    if args.web:
        # Si on fournit un export, on lance l’export en tâche de fond en même temps que Flask.
        if args.export_csv or args.export_jsonl:
            start_background_export(args.interval, args.export_csv, args.export_jsonl)
        # Start background session cleaner
        try:
            # allow disabling public read mode via env
            PUBLIC_READ = os.environ.get("PUBLIC_READ", "false").lower() in ("1", "true", "yes")
            start_session_cleaner(interval=60)
        except Exception as e:
            logging.error(f"Erreur lancement session cleaner : {e}")
        # (L'ouverture automatique du navigateur est désactivée sur Render)
        app.run(host=args.host, port=args.port, debug=False)
    else:
        run_cli(args.interval, args.export_csv, args.export_jsonl)


if __name__ == "__main__":
    main()
