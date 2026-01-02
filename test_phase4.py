import requests
import json
import time

token = "api_4a8cc8952229446881d5"
url = "http://127.0.0.1:5000/api/actions/queue"

# Test 1: Queue message action
print("\n=== TEST 1: Queue Message Action ===")
data = {
    "machine_id": "test-pc",
    "action_type": "message",
    "data": {
        "message": "🎉 Ceci est un test Phase 4! (envoyé à " + time.strftime("%H:%M:%S") + ")",
        "title": "DashFleet Action Test"
    }
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code in (200, 201):
    action_id = response.json().get("action_id")
    print(f"\n✅ Action queued successfully!")
    print(f"Action ID: {action_id}")
    
    # Test 2: Agent polls for pending actions
    print("\n=== TEST 2: Agent Polls Pending Actions ===")
    poll_url = f"http://127.0.0.1:5000/api/actions/pending?machine_id=test-pc"
    poll_response = requests.get(poll_url, headers=headers)
    print(f"Status: {poll_response.status_code}")
    print(f"Pending actions: {json.dumps(poll_response.json(), indent=2)}")
    
    # Test 3: Agent reports result
    if poll_response.status_code == 200 and poll_response.json().get("actions"):
        print("\n=== TEST 3: Agent Reports Result ===")
        report_url = "http://127.0.0.1:5000/api/actions/report"
        report_data = {
            "action_id": action_id,
            "status": "done",
            "result": "Message displayed successfully (Windows MessageBox)"
        }
        report_response = requests.post(report_url, json=report_data, headers=headers)
        print(f"Status: {report_response.status_code}")
        print(f"Response: {json.dumps(report_response.json(), indent=2)}")
else:
    print(f"❌ Error: {response.text}")
