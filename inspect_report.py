#!/usr/bin/env python3
import sqlite3
import json

db = sqlite3.connect('data/fleet.db')

print("=" * 80)
print("=== INSPECTION D'UN RAPPORT COMPLET ===")
print("=" * 80)

row = db.execute('SELECT id, report, ts, org_id FROM fleet ORDER BY ts DESC LIMIT 1').fetchone()
if row:
    print(f"\nID: {row[0]}")
    print(f"Timestamp: {row[2]}")
    print(f"Org ID: {row[3]}")
    print(f"\nRapport brut (type: {type(row[1])}):")
    print(repr(row[1]))
    
    try:
        report = json.loads(row[1])
        print("\n✅ JSON valide. Contenu:")
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(f"\n❌ Erreur JSON: {e}")
else:
    print("❌ Aucune donnée dans fleet")

db.close()
