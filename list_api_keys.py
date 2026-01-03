#!/usr/bin/env python3
import sqlite3

db = sqlite3.connect('data/fleet.db')

print("=" * 80)
print("🔑 CLÉS API DASHFLEET")
print("=" * 80)
print()

rows = db.execute('''
    SELECT api_keys.key, api_keys.org_id, organizations.name, api_keys.revoked 
    FROM api_keys 
    LEFT JOIN organizations ON api_keys.org_id = organizations.id
    ORDER BY api_keys.created_at DESC
''').fetchall()

if rows:
    for i, row in enumerate(rows, 1):
        key = row[0]
        org_id = row[1]
        org_name = row[2] or "N/A"
        revoked = row[3]
        status = "❌ RÉVOQUÉE" if revoked else "✅ ACTIVE"
        
        print(f"Clé #{i}:")
        print(f"  🔑 Clé API:      {key}")
        print(f"  🏢 Organisation: {org_name} ({org_id})")
        print(f"  📊 Status:       {status}")
        print()
else:
    print("  ❌ Aucune clé API trouvée")
    print()

print("=" * 80)
print("💡 Pour utiliser une clé dans le dashboard:")
print("   1. Ouvrir: https://dash-fleet.com/fleet")
print("   2. Appuyer sur F12 (Console)")
print("   3. Taper: sessionStorage.setItem('api_key', 'VOTRE_CLÉ');")
print("   4. Recharger la page")
print("=" * 80)

db.close()
