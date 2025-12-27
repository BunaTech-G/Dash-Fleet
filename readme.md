# System Dashboard (Python + Flask)

Small learning project that monitors CPU, RAM, disk, and uptime with both CLI output and a minimal Flask web UI. Metrics come from `psutil` and optional alerts fire when CPU >= 80% or RAM >= 90%.

## Contents
- [main.py](main.py) — CLI runner and Flask app
- [templates/index.html](templates/index.html) — Web UI
- [static/style.css](static/style.css) — Styling for the dashboard
- [requirements.txt](requirements.txt) — Python dependencies

## Prerequisites
- Python 3.10+ recommended
- `pip` available

## Setup
1) Create and activate a virtual env (Windows PowerShell):
```
python -m venv .venv
.venv\Scripts\Activate
```

2) Install dependencies:
```
pip install -r requirements.txt
```

## Run (CLI mode)
Print metrics to the terminal every 2 seconds:
```
python main.py
```

Options:
- `--interval 1.5` — change refresh interval (seconds)
- `--export-csv logs/metrics.csv` — append snapshots to CSV
- `--export-jsonl logs/metrics.jsonl` — append snapshots as JSON Lines

Stop anytime with `Ctrl+C`.

## Run (Web dashboard)
Start the Flask UI on http://127.0.0.1:5000:
```
python main.py --web
```

Options:
- `--host 0.0.0.0` — listen on all interfaces
- `--port 8000` — custom port

The page auto-refreshes every ~2.5 seconds. A red badge appears when alerts trigger.

## What the code does
- Collects CPU, RAM, disk, and uptime with `psutil` ([main.py](main.py))
- Formats uptime as `HH:MM:SS` and converts bytes to GiB for readability
- Flags alerts for CPU/RAM thresholds and surfaces them in CLI + web
- Exposes `/api/stats` JSON endpoint for reuse ([main.py](main.py))
- Optional CSV/JSONL logging helpers for later analysis ([main.py](main.py))

## Quick learning notes
- `psutil.cpu_percent(interval=0.3)` waits briefly to return a real sample instead of 0 on the first call.
- Disk usage targets your OS root (home drive on Windows) so the numbers are stable.
- JSONL (one JSON object per line) is handy for streaming logs; most tools can read it line by line.

## Testing the project
- CLI: run `python main.py --interval 1` and verify stats update and alerts toggle when you stress CPU/RAM.
- Web: start with `python main.py --web`, open the browser, and ensure values refresh every few seconds.
- Exports: run `python main.py --export-csv logs/out.csv --export-jsonl logs/out.jsonl`, let it run for 5+ samples, then open the files to confirm headers/lines exist.

## Next ideas
- Add a /history view that reads the CSV/JSONL and charts it.
- Add Windows service or systemd unit to keep the exporter running.
- Package as a Docker image with health endpoints.
