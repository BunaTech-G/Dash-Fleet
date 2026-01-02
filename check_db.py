#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

db = sqlite3.connect('data/fleet.db')

print("=" * 60)
print("=== MACHINES DANS LA BASE ===")
print("=" * 60)
rows = db.execute('SELECT id, report, ts, org_id FROM fleet ORDER BY ts DESC LIMIT 10').fetchall()
if rows:
    for row in rows:
        report = json.loads(row[1])
        machine_id = report.get('machine_id', 'N/A')
        cpu = report.get('cpu', 'N/A')
        ts = datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')
        org_id = row[3]
        print(f"  {machine_id:20} | CPU:{cpu:5}% | {ts} | org:{org_id}")
else:
    print("  ❌ Aucune machine enregistrée")

print("\n" + "=" * 60)
print("=== API KEYS ===")
print("=" * 60)
rows = db.execute('SELECT key, org_id, created_at, revoked FROM api_keys').fetchall()
if rows:
    for row in rows:
        key_preview = row[0][:30] + "..."
        org_id = row[1]
        revoked = "❌ REVOKED" if row[3] else "✅ ACTIVE"
        print(f"  {key_preview:35} | org:{org_id:20} | {revoked}")
else:
    print("  ❌ Aucune clé API enregistrée")

print("\n" + "=" * 60)
print("=== ORGANIZATIONS ===")
print("=" * 60)
rows = db.execute('SELECT id, name FROM organizations').fetchall()
if rows:
    for row in rows:
        print(f"  {row[0]:30} | {row[1]}")
else:
    print("  ❌ Aucune organisation")

db.close()
