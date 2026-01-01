#!/usr/bin/env python3
"""Migre `logs/fleet_state.json` vers un fichier SQLite `data/fleet.db`.

Usage:
  python scripts/migrate_fleet_to_sqlite.py

Le script crée `data/fleet.db` et une table `fleet(id TEXT PRIMARY KEY, report JSON, ts REAL, client TEXT)`.
"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / 'logs' / 'fleet_state.json'
DB_PATH = ROOT / 'data' / 'fleet.db'


def ensure_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fleet (
            id TEXT PRIMARY KEY,
            report TEXT,
            ts REAL,
            client TEXT
        )
        """
    )
    conn.commit()
    return conn


def load_json(path: Path):
    if not path.exists():
        print('No fleet_state.json found at', path)
        return {}
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def migrate():
    data = load_json(LOG_PATH)
    if not data:
        print('No data to migrate')
        return

    conn = ensure_db(DB_PATH)
    cur = conn.cursor()
    count = 0
    for mid, entry in data.items():
        report_json = json.dumps(entry.get('report', {}), ensure_ascii=False)
        ts = entry.get('ts', None)
        client = entry.get('client', None)
        cur.execute(
            'INSERT OR REPLACE INTO fleet (id, report, ts, client) VALUES (?, ?, ?, ?)',
            (mid, report_json, ts, client),
        )
        count += 1
    conn.commit()
    conn.close()
    print(f'Migrated {count} entries to {DB_PATH}')


if __name__ == '__main__':
    migrate()
