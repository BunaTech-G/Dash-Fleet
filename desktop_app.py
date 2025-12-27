"""Application bureau (Tkinter) pour surveiller CPU/RAM/Disque/Uptime.
- UI native (pas de navigateur)
- Rafraîchissement périodique
- Alerte visuelle si CPU>=80% ou RAM>=90%
- Export CSV optionnel (Desktop/metrics_desktop.csv par défaut)
"""
from __future__ import annotations

import csv
import datetime as dt
import threading
import time
from pathlib import Path
from typing import Dict

import psutil
import tkinter as tk
from tkinter import ttk, messagebox

CPU_ALERT = 80.0
RAM_ALERT = 90.0
REFRESH_INTERVAL = 2000  # ms
EXPORT_PATH_DEFAULT = Path.home() / "Desktop" / "metrics_desktop.csv"


def format_bytes_to_gib(bytes_value: float) -> float:
    return round(bytes_value / (1024 ** 3), 2)


def format_uptime(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def collect_stats() -> Dict[str, object]:
    cpu_percent = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor or "/")
    uptime_seconds = time.time() - psutil.boot_time()

    alerts = {
        "cpu": cpu_percent >= CPU_ALERT,
        "ram": ram.percent >= RAM_ALERT,
    }

    return {
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "cpu_percent": cpu_percent,
        "ram_percent": ram.percent,
        "ram_used_gib": format_bytes_to_gib(ram.used),
        "ram_total_gib": format_bytes_to_gib(ram.total),
        "disk_percent": disk.percent,
        "disk_used_gib": format_bytes_to_gib(disk.used),
        "disk_total_gib": format_bytes_to_gib(disk.total),
        "uptime_seconds": uptime_seconds,
        "uptime_hms": format_uptime(uptime_seconds),
        "alerts": alerts,
        "alert_active": any(alerts.values()),
    }


def export_to_csv(csv_path: Path, row: Dict[str, object]) -> None:
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


class DashboardApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Dashboard système (desktop)")
        self.root.geometry("520x360")
        self.root.configure(bg="#0f172a")
        self.export_enabled = tk.BooleanVar(value=True)
        self.export_path = tk.StringVar(value=str(EXPORT_PATH_DEFAULT))

        self._build_ui()
        self._schedule_refresh()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a", foreground="#e5e7eb")
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Value.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Muted.TLabel", foreground="#9ca3af")
        style.configure("TButton", padding=6)

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Tableau de bord système (desktop)", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="CPU, RAM, Disque, Uptime", style="Muted.TLabel").pack(anchor="w")

        grid = ttk.Frame(main)
        grid.pack(fill="x", pady=4)

        self.labels = {}
        rows = [
            ("CPU", "cpu_percent", "%"),
            ("RAM", "ram_percent", "%"),
            ("Disque", "disk_percent", "%"),
            ("Uptime", "uptime_hms", ""),
        ]
        for i, (title, key, suffix) in enumerate(rows):
            frame = ttk.Frame(grid, relief="ridge", padding=8)
            frame.grid(row=0, column=i, padx=6, sticky="nsew")
            grid.columnconfigure(i, weight=1)
            ttk.Label(frame, text=title, style="Muted.TLabel").pack(anchor="w")
            val = ttk.Label(frame, text="--", style="Value.TLabel")
            val.pack(anchor="w")
            meta = ttk.Label(frame, text="", style="Muted.TLabel")
            meta.pack(anchor="w")
            self.labels[key] = (val, meta, suffix)

        # Export controls
        export_frame = ttk.Frame(main)
        export_frame.pack(fill="x", pady=(12, 4))
        ttk.Checkbutton(export_frame, text="Exporter CSV", variable=self.export_enabled).pack(side="left")
        ttk.Entry(export_frame, textvariable=self.export_path, width=45).pack(side="left", padx=8)
        ttk.Button(export_frame, text="Par défaut Bureau", command=self._reset_export_path).pack(side="left")

        # Status
        self.status = ttk.Label(main, text="En attente des données", style="Muted.TLabel")
        self.status.pack(anchor="w", pady=(10, 0))

    def _reset_export_path(self) -> None:
        self.export_path.set(str(EXPORT_PATH_DEFAULT))

    def _update_cards(self, stats: Dict[str, object]) -> None:
        for key, (val_label, meta_label, suffix) in self.labels.items():
            if key == "cpu_percent":
                val_label.configure(text=f"{stats['cpu_percent']:.1f}{suffix}")
                meta_label.configure(text="Alerte" if stats["alerts"]["cpu"] else "")
            elif key == "ram_percent":
                val_label.configure(text=f"{stats['ram_percent']:.1f}{suffix}")
                meta_label.configure(text=f"{stats['ram_used_gib']:.2f}/{stats['ram_total_gib']:.2f} GiB")
                if stats["alerts"]["ram"]:
                    meta_label.configure(text=meta_label.cget("text") + " • Alerte")
            elif key == "disk_percent":
                val_label.configure(text=f"{stats['disk_percent']:.1f}{suffix}")
                meta_label.configure(text=f"{stats['disk_used_gib']:.2f}/{stats['disk_total_gib']:.2f} GiB")
            elif key == "uptime_hms":
                val_label.configure(text=str(stats['uptime_hms']))
                meta_label.configure(text="")

        # Couleur d’alerte : fond de fenêtre
        if stats["alert_active"]:
            self.root.configure(bg="#2a0f16")
        else:
            self.root.configure(bg="#0f172a")

    def _refresh(self) -> None:
        try:
            stats = collect_stats()
            self._update_cards(stats)
            self.status.configure(text=f"{stats['timestamp']}")
            if self.export_enabled.get():
                export_to_csv(Path(self.export_path.get()), stats)
        except Exception as exc:  # noqa: BLE001
            self.status.configure(text=f"Erreur: {exc}")

        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        self.root.after(REFRESH_INTERVAL, self._refresh)


def run_app() -> None:
    root = tk.Tk()
    DashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
