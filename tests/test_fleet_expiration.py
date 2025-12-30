"""Test d'expiration simple utilisant pytest.

Procédure:
- Le serveur Flask doit être lancé.
- Le test POSTe un rapport, modifie le backup JSON (`logs/fleet_state.json`) pour rendre l'entrée ancienne,
  puis appelle `POST /api/fleet/reload` (protégé par `FLEET_TOKEN`) et vérifie que l'entrée est listée en `expired`.
"""

import json
import os
import time
import urllib.request
import urllib.error
import pytest

SERVER = os.environ.get("TEST_SERVER", "http://localhost:5000")
TOKEN = os.environ.get("FLEET_TOKEN")
MACHINE_ID = "test-expire-001"


def _req(url: str, data: bytes | None, headers: dict, method: str = "POST"):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.getcode(), resp.read()


def test_fleet_expiration_flow():
    if not TOKEN:
        pytest.skip("FLEET_TOKEN not set in environment for test")

    post_url = SERVER.rstrip('/') + '/api/fleet/report'
    get_url = SERVER.rstrip('/') + '/api/fleet'
    reload_url = SERVER.rstrip('/') + '/api/fleet/reload'
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
    code, _ = _req(post_url, json.dumps(payload).encode('utf-8'), headers, method='POST')
    assert code == 200

    # Wait briefly for server to persist
    time.sleep(0.5)

    state_path = os.path.join('logs', 'fleet_state.json')
    assert os.path.exists(state_path), "fleet_state.json not found"

    with open(state_path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    assert MACHINE_ID in data, "machine not present in state after POST"

    # make the entry old
    old_ts = int(time.time()) - 3600
    data[MACHINE_ID]['ts'] = old_ts
    # Prefer updating SQLite if present (main now writes DB), otherwise update JSON backup
    db_path = os.path.join('data', 'fleet.db')
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # ensure row exists; update ts
        cur.execute('UPDATE fleet SET ts = ? WHERE id = ?', (old_ts, MACHINE_ID))
        conn.commit()
        cur.execute('SELECT ts FROM fleet WHERE id = ?', (MACHINE_ID,))
        row = cur.fetchone()
        conn.close()
        # if update didn't stick (locked or missing row), fallback to JSON write below
        if not row or int(row[0]) != int(old_ts):
            with open(state_path, 'w', encoding='utf-8') as fh:
                json.dump(data, fh)
    else:
        with open(state_path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh)

    # Force server to reload from backup (requires token)
    code, raw = _req(reload_url, b'{}', headers, method='POST')
    assert code == 200

    # Now ask fleet; the server should have purged expired entries
    # allow a short retry window
    for _ in range(5):
        try:
            code, raw = _req(get_url, None, headers, method='GET')
            if code == 200:
                body = json.loads(raw.decode('utf-8'))
                expired = body.get('expired', [])
                data_ids = [d.get('id') for d in body.get('data', [])]
                if MACHINE_ID in expired or MACHINE_ID not in data_ids:
                    return
            # otherwise wait and retry
        except Exception:
            pass
        time.sleep(0.5)

    # final check: ensure the machine was purged (either listed as expired or absent from data)
    code, raw = _req(get_url, None, headers, method='GET')
    assert code == 200, f"Unexpected status code {code} when querying fleet"
    body = json.loads(raw.decode('utf-8'))
    expired = body.get('expired', [])
    data_ids = [d.get('id') for d in body.get('data', [])]
    assert MACHINE_ID in expired or MACHINE_ID not in data_ids, f"Machine {MACHINE_ID} not expired/removed, response: {body}"
