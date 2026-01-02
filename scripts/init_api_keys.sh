#!/bin/bash
# Initialize API keys for dashboard and agents
# Run once after deployment to ensure org_default has an API key

cd /opt/dashfleet

python3 << 'PYEOF'
import sqlite3
import uuid
import time
import sys

try:
    conn = sqlite3.connect('data/fleet.db')
    c = conn.cursor()
    
    # Check if org_default exists
    c.execute('SELECT id FROM organizations WHERE id = ?', ('org_default',))
    if not c.fetchone():
        print("✓ Creating org_default...")
        c.execute('INSERT INTO organizations (id, name) VALUES (?, ?)', 
                  ('org_default', 'Default Organization'))
        conn.commit()
    
    # Check if org_default has an API key
    c.execute('SELECT key FROM api_keys WHERE org_id = ? AND revoked = 0 LIMIT 1', ('org_default',))
    key = c.fetchone()
    
    if not key:
        print("✓ Creating API key for org_default...")
        api_key = 'api_' + str(uuid.uuid4()).replace('-', '')[:20]
        c.execute('INSERT INTO api_keys (key, org_id, created_at, revoked) VALUES (?, ?, ?, 0)',
                  (api_key, 'org_default', time.time()))
        conn.commit()
        print(f"  Key: {api_key}")
    else:
        print(f"✓ API key exists: {key[0][:12]}...")
    
    conn.close()
    print("✓ Initialization complete!")
    
except Exception as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
