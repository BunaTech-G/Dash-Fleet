"""Test d'expiration : poste présent puis modifié pour paraitre ancien -> serveur doit purger lors d'un GET /api/fleet
Procédure:
- Le serveur Flask doit être lancé.
- Le test POSTe un rapport, lit logs/fleet_state.json, modifie le ts pour le rendre ancien (> TTL), sauvegarde, puis appelle GET /api/fleet et attend que l'entrée soit purgée.
"""
import json
import os
import time
import urllib.request

SERVER = os.environ.get("TEST_SERVER", "http://localhost:5000")
TOKEN = os.environ.get("FLEET_TOKEN")
MACHINE_ID = "test-expire-001"

if not TOKEN:
    print("FLEET_TOKEN not set in environment for test")
    raise SystemExit(1)

post_url = SERVER.rstrip('/') + '/api/fleet/report'
get_url = SERVER.rstrip('/') + '/api/fleet'
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'}

payload = {
    'machine_id': MACHINE_ID,
    'report': {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'cpu_percent': 1.0,
        'ram_percent': 2.0,
        'disk_percent': 3.0,
        'uptime_hms': '00:00:10',
        'health': {'score': 100, 'status': 'ok'},
    }
}

# Post report
req = urllib.request.Request(post_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
with urllib.request.urlopen(req, timeout=5) as resp:
    print('POST', resp.getcode())

# Wait short time
time.sleep(0.5)

state_path = os.path.join('logs', 'fleet_state.json')
if not os.path.exists(state_path):
    print('fleet_state.json not found')
    raise SystemExit(2)

# Modify ts to be old
with open(state_path, 'r', encoding='utf-8') as fh:
    data = json.load(fh)

if MACHINE_ID not in data:
    print('machine not in state after post')
    raise SystemExit(3)

old_ts = int(time.time()) - 3600
data[MACHINE_ID]['ts'] = old_ts
with open(state_path, 'w', encoding='utf-8') as fh:
    json.dump(data, fh)

# call GET /api/fleet which should purge expired entries
with urllib.request.urlopen(get_url, timeout=5) as resp:
    body = json.loads(resp.read().decode('utf-8'))
    expired = body.get('expired', [])
    if MACHINE_ID in expired:
        print('EXPIRATION OK')
        raise SystemExit(0)
    else:
        print('Not expired according to server, response:', body)
        raise SystemExit(4)
