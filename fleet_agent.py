#!/usr/bin/env python3
"""Agent léger qui remonte des métriques vers /api/fleet/report.
- Nécessite psutil.
- Utilise FLEET_TOKEN pour l'authentification.
"""
import argparse
import ctypes
import json
import logging
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
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

        # System information metadata
        "system": {
            "os": platform.system(),
            "os_version": platform.release(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "hardware_id": hex(uuid.getnode()),
        }
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


def send_heartbeat(server: str, token: str, machine_id: str, hardware_id: str) -> bool:
    """Send lightweight heartbeat ping (no metrics)."""
    payload = {
        "machine_id": machine_id,
        "hardware_id": hardware_id,
        "timestamp": time.time()
    }
    data = json.dumps(payload).encode("utf-8")
    url_ping = server.rstrip("/") + "/api/fleet/ping"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url_ping, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            ok = 200 <= resp.getcode() < 300
            return ok
    except Exception:
        return False


# ============================================================================
# ACTION HANDLERS (Phase 4)
# ============================================================================

def get_pending_actions(server: str, token: str, machine_id: str) -> list:
    """Poll for pending actions."""
    url = f"{server.rstrip('/')}/api/actions/pending?machine_id={machine_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("actions", [])
    except Exception as e:
        logging.debug(f"Get pending actions failed: {e}")
        return []


def execute_action(action: dict) -> tuple[bool, str]:
    """Execute an action and return (success, result_message)."""
    action_type = action.get("type")
    data = action.get("data", {})

    if action_type == "message":
        message = data.get("message", "No message")
        title = data.get("title", "DashFleet")
        return execute_message(message, title)

    elif action_type == "restart":
        return execute_restart()

    elif action_type == "reboot":
        return execute_reboot()

    else:
        return False, f"Unknown action type: {action_type}"


def execute_message(message: str, title: str = "DashFleet") -> tuple[bool, str]:
    """Display a message box (OS-specific)."""
    try:
        if platform.system() == "Windows":
            ctypes.windll.user32.MessageBoxW(
                0, message, title, 
                0x1000 | 0x40  # MB_SYSTEMMODAL | MB_ICONINFORMATION
            )
            return True, "Message displayed (Windows)"

        elif platform.system() == "Linux":
            try:
                subprocess.run(
                    ["notify-send", title, message],
                    timeout=5,
                    capture_output=True
                )
                return True, "Notification sent (notify-send)"
            except BaseException:
                try:
                    subprocess.run(
                        ["zenity", "--info", "--title", title, "--text", message],
                        timeout=5,
                        capture_output=True
                    )
                    return True, "Dialog shown (zenity)"
                except BaseException:
                    return False, "No notification system found (install notify-send or zenity)"

        elif platform.system() == "Darwin":  # macOS
            try:
                cmd = f'osascript -e \'display notification "{message}" with title "{title}\"\''
                os.system(cmd)
                return True, "Notification sent (macOS)"
            except Exception as e:
                return False, str(e)

        else:
            return False, f"Unsupported OS: {platform.system()}"

    except Exception as e:
        return False, f"Message execution failed: {str(e)}"


def execute_restart() -> tuple[bool, str]:
    """Restart the agent process."""
    try:
        logging.info("Restarting agent...")
        os.execvp(sys.executable, [sys.executable] + sys.argv)
        return True, "Agent restarted"
    except Exception as e:
        return False, f"Restart failed: {str(e)}"


def execute_reboot() -> tuple[bool, str]:
    """Reboot the machine."""
    try:
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
            return True, "Reboot scheduled (60 seconds)"
        else:
            subprocess.run(["sudo", "shutdown", "-r", "+1"], check=True)
            return True, "Reboot scheduled (1 minute)"
    except Exception as e:
        return False, f"Reboot command failed: {str(e)}"


def report_action_result(server: str, token: str, action_id: str, 
                         status: str, result: str) -> bool:
    """Report action execution result to server."""
    url = f"{server.rstrip('/')}/api/actions/report"
    payload = {
        "action_id": action_id,
        "status": status,
        "result": result
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}"
    }

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.getcode() < 300
    except Exception as e:
        logging.error(f"Report action result failed: {e}")
        return False


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
    parser.add_argument("--tray", action="store_true", help="Afficher une icône systray Windows avec les métriques")
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

    # Import and start tray icon if requested (Windows only)
    tray_icon = None
    if args.tray:
        try:
            from fleet_agent_windows_tray import run_tray_icon
            import threading
            
            # Run tray in background thread
            tray_thread = threading.Thread(
                target=lambda: run_tray_icon(collect_agent_stats),
                daemon=True
            )
            tray_thread.start()
            log_line("[TRAY] Icône systray démarrée (cliquez sur l'icône en bas à droite)")
        except ImportError:
            log_line("[TRAY] ⚠️  pystray/pillow non installés. Installez: pip install pystray pillow")
        except Exception as e:
            log_line(f"[TRAY] ⚠️  Erreur tray: {e}")

    url = server.rstrip("/") + path
    hardware_id = hex(uuid.getnode())

    log_line(f"Agent démarré -> {url}")
    log_line(f"id={machine_id}, intervalle={interval}s, hardware_id={hardware_id}")

    cycle = 0
    action_poll_counter = 0
    while True:
        report = collect_agent_stats()
        ok, msg = post_report(url, token, machine_id, report)
        status = "OK" if ok else "KO"
        short = f"CPU {report['cpu_percent']:.1f}% RAM {report['ram_percent']:.1f}% Disk {report['disk_percent']:.1f}%"
        if ok:
            log_line(f"[{time.strftime('%H:%M:%S')}] {status} {msg} | {short} | Score {report['health']['score']}/100")
        else:
            log_line(f"[{time.strftime('%H:%M:%S')}] {status} {msg} | ERREUR d'envoi | {short}")

        # Every 5 cycles (5 × interval), send heartbeat
        cycle += 1
        if cycle % 5 == 0:
            hb_ok = send_heartbeat(server, token, machine_id, hardware_id)
            if not hb_ok:
                log_line(f"[{time.strftime('%H:%M:%S')}] Heartbeat FAILED")

        # Poll for actions every ~30 seconds (every 3 cycles if interval=10s)
        action_poll_counter += 1
        if action_poll_counter >= 3:
            actions = get_pending_actions(server, token, machine_id)
            for action in actions:
                action_id = action.get("action_id")
                try:
                    success, result = execute_action(action)
                    status_report = "done" if success else "error"
                    report_action_result(server, token, action_id, status_report, result)
                    log_line(f"[{time.strftime('%H:%M:%S')}] Action {action_id} executed: {result}")
                except Exception as e:
                    log_line(f"[{time.strftime('%H:%M:%S')}] Action {action_id} failed: {e}")
                    report_action_result(server, token, action_id, "error", str(e))

            action_poll_counter = 0

        # Si le serveur est injoignable, on attend mais on ne quitte pas
        time.sleep(max(1.0, interval))


if __name__ == "__main__":
    main()
