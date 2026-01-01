import os
import time
import json
import threading
import urllib.request
import urllib.error
import pytest

SERVER = os.environ.get("TEST_SERVER", "http://localhost:5000")
ACTION_TOKEN = os.environ.get("ACTION_TOKEN")

NUM_AGENTS = 5


def _req(url: str, data: bytes | None, headers: dict, method: str = "POST"):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.getcode(), resp.read()


@pytest.mark.skipif(not ACTION_TOKEN, reason="ACTION_TOKEN not set")
def test_multi_agents_report():
    # Create an organization to get an api_key
    create_url = SERVER.rstrip('/') + '/api/orgs'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ACTION_TOKEN}'}
    payload = json.dumps({'name': 'test-multi-agents'}).encode('utf-8')
    code, raw = _req(create_url, payload, headers, method='POST')
    assert code == 200
    body = json.loads(raw.decode('utf-8'))
    api_key = body.get('api_key')
    assert api_key

    # function for agent thread
    def agent_thread(mid: str):
        url = SERVER.rstrip('/') + '/api/fleet/report'
        hdr = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
        report = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'cpu_percent': 1.0,
        }
        payload = json.dumps({'machine_id': mid, 'report': report}).encode('utf-8')
        try:
            c, _ = _req(url, payload, hdr, method='POST')
            assert c == 200
        except Exception as e:
            pytest.fail(f'Agent {mid} failed: {e}')

    threads = []
    for i in range(NUM_AGENTS):
        mid = f"multi-test-{i}"
        t = threading.Thread(target=agent_thread, args=(mid,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # allow server to persist
    time.sleep(0.5)

    # query fleet using the org api_key
    get_url = SERVER.rstrip('/') + '/api/fleet'
    hdr = {'Authorization': f'Bearer {api_key}'}
    code, raw = _req(get_url, None, hdr, method='GET')
    assert code == 200
    body = json.loads(raw.decode('utf-8'))
    ids = [d.get('id') for d in body.get('data', [])]
    for i in range(NUM_AGENTS):
        assert f"multi-test-{i}" in ids
