"""Test simple pour vérifier la persistance de la flotte.
Procédure :
- Le serveur Flask doit être lancé localement (http://localhost:5000) et écrire `logs/fleet_state.json`.
- Exécuter ce script : il POSTe un rapport, attend, puis vérifie que `logs/fleet_state.json` contient `machine_id`.
"""
import json
import os
import time
import urllib.request
import pytest

SERVER = os.environ.get("TEST_SERVER", "http://localhost:5000")
TOKEN = os.environ.get("FLEET_TOKEN")
MACHINE_ID = "test-persistence-001"


def test_fleet_persistence():
    if not TOKEN:
        pytest.skip("FLEET_TOKEN not set in environment for test")

    url = SERVER.rstrip('/') + '/api/fleet/report'
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

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.getcode() == 200

    # give server small time to write file
    time.sleep(0.5)

    state_path = os.path.join('logs', 'fleet_state.json')
    assert os.path.exists(state_path), 'fleet_state.json not found'

    with open(state_path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    assert MACHINE_ID in data, 'Machine id not present in persistent state after POST'
