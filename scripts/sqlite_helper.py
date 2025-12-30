#!/usr/bin/env python3
"""Simple helper to query the fleet SQLite database created by the migration script."""
import sqlite3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data' / 'fleet.db'


def list_all():
    if not DB_PATH.exists():
        print('DB not found:', DB_PATH)
        return []
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute('SELECT id, report, ts, client FROM fleet')
    rows = cur.fetchall()
    conn.close()
    results = []
    for r in rows:
        try:
            report = json.loads(r[1])
        except Exception:
            report = {}
        results.append({'id': r[0], 'report': report, 'ts': r[2], 'client': r[3]})
    return results


if __name__ == '__main__':
    for e in list_all():
        print(e['id'], 'ts=', e['ts'])
