# 🎯 PHASE 4 ACTION PLAN - Message/Action System

**Date:** 2 janvier 2026  
**Objectif:** Ajouter système de messages et commandes aux agents  
**Durée estimée:** 7-8 heures  
**Priorité:** 🔴 Important pour fleet management  

---

## 📋 Résumé du Système

**Concept:** Envoyer des messages/commandes à des agents via une file d'attente (SQLite)
- Dashboard → POST /api/actions/queue → SQLite actions table
- Agent → GET /api/actions/pending (polling chaque 30s)
- Agent → Exécute action (message, restart, reboot)
- Agent → POST /api/actions/report (résultat)

**Architecture de polling:**
```
Dashboard     Agent              API/DB
   │           │                  │
   │─── POST action ────────────→ │
   │           │                  │
   │           │← GET pending ────│
   │           │ (every 30s)      │
   │           │                  │
   │           ├─ Execute ────────┤
   │           │                  │
   │           │─ POST result ───→│
   │           │                  │
```

---

## 📍 Phase Breakdown

### Phase 4.1: Database Schema (30 minutes) 🔴 CRITICAL

**File:** `data/fleet.db` (add new table)

**SQL to Execute:**
```sql
-- Create actions table
CREATE TABLE IF NOT EXISTS actions (
    id TEXT PRIMARY KEY,              -- "org:machine:timestamp"
    org_id TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    action_type TEXT NOT NULL,        -- "message", "restart", "reboot"
    payload TEXT NOT NULL,            -- JSON blob with action data
    status TEXT DEFAULT 'pending',    -- pending, executing, done, error
    result TEXT,                      -- Execution result message
    created_by TEXT,                  -- Admin who created it
    created_at REAL NOT NULL,         -- timestamp
    executed_at REAL,                 -- timestamp when executed
    FOREIGN KEY (org_id) REFERENCES organizations(id)
);

-- Create index for agent polling
CREATE INDEX IF NOT EXISTS idx_actions_pending 
    ON actions(machine_id, org_id, status);

-- Create index for recent actions
CREATE INDEX IF NOT EXISTS idx_actions_recent 
    ON actions(created_at DESC);
```

**Implementation:**
```python
# Create small script to initialize schema
# scripts/init_actions_table.py

import sqlite3
from pathlib import Path

DB_PATH = Path("data/fleet.db")

def init_actions_table():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_by TEXT,
            created_at REAL NOT NULL,
            executed_at REAL,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
    ''')
    
    # Create indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_actions_pending 
        ON actions(machine_id, org_id, status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_actions_recent 
        ON actions(created_at DESC)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Actions table initialized")

if __name__ == "__main__":
    init_actions_table()
```

---

### Phase 4.2: API Endpoints (2 hours) 🔴 CRITICAL

**File:** `main.py`

**Add 3 new endpoints:**

#### Endpoint 1: Queue Action (POST)
```python
@app.route("/api/actions/queue", methods=["POST"])
@limiter.limit("100/minute")
def queue_action():
    """Queue an action to execute on a machine."""
    # Require admin token or org auth
    ok, org_id = _check_org_key()
    if not ok:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        payload = request.get_json(force=True)
        machine_id = payload.get("machine_id")
        action_type = payload.get("action_type")  # "message", "restart", "reboot"
        action_data = payload.get("data", {})     # Action-specific data
        
        if not machine_id or not action_type:
            return jsonify({"error": "Missing machine_id or action_type"}), 400
        
        # Validate action_type
        valid_types = ["message", "restart", "reboot"]
        if action_type not in valid_types:
            return jsonify({"error": f"Invalid action_type. Must be one of: {valid_types}"}), 400
    
    except Exception as e:
        logging.error(f"Queue action parse error: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    
    try:
        action_id = f"{org_id}:{machine_id}:{int(time.time()*1000)}"
        
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO actions 
            (id, org_id, machine_id, action_type, payload, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            action_id,
            org_id,
            machine_id,
            action_type,
            json.dumps(action_data),
            'pending',
            'dashboard_user',  # TODO: Get from session
            time.time()
        ))
        conn.commit()
        conn.close()
        
        logging.info(f"Action queued: {action_id} ({action_type}) for {machine_id}")
        return jsonify({"ok": True, "action_id": action_id}), 201
        
    except Exception as e:
        logging.error(f"Queue action failed: {e}")
        return jsonify({"error": str(e)}), 500
```

#### Endpoint 2: Get Pending Actions (GET)
```python
@app.route("/api/actions/pending")
@limiter.limit("60/minute")
def get_pending_actions():
    """Agent polls for pending actions for this machine."""
    ok, org_id = _check_org_key()
    if not ok:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        machine_id = request.args.get("machine_id")
        if not machine_id:
            return jsonify({"error": "machine_id query param required"}), 400
        
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, action_type, payload 
            FROM actions
            WHERE org_id = ? AND machine_id = ? AND status = 'pending'
            ORDER BY created_at ASC
            LIMIT 10
        ''', (org_id, machine_id))
        
        actions = []
        for row in cursor.fetchall():
            try:
                action_data = json.loads(row[2])
            except:
                action_data = {}
            
            actions.append({
                "action_id": row[0],
                "type": row[1],
                "data": action_data
            })
        
        conn.close()
        
        logging.debug(f"Pending actions for {machine_id}: {len(actions)}")
        return jsonify({"actions": actions})
        
    except Exception as e:
        logging.error(f"Get pending actions failed: {e}")
        return jsonify({"error": str(e)}), 500
```

#### Endpoint 3: Report Action Result (POST)
```python
@app.route("/api/actions/report", methods=["POST"])
@limiter.limit("60/minute")
def report_action_result():
    """Agent reports action execution result."""
    ok, org_id = _check_org_key()
    if not ok:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        payload = request.get_json(force=True)
        action_id = payload.get("action_id")
        status = payload.get("status")  # "done" or "error"
        result = payload.get("result", "")
        
        if not action_id or not status:
            return jsonify({"error": "Missing action_id or status"}), 400
        
        if status not in ["done", "error"]:
            return jsonify({"error": "Invalid status. Must be 'done' or 'error'"}), 400
    
    except Exception as e:
        logging.error(f"Report action parse error: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE actions 
            SET status = ?, result = ?, executed_at = ?
            WHERE id = ? AND org_id = ?
        ''', (status, result, time.time(), action_id, org_id))
        conn.commit()
        conn.close()
        
        logging.info(f"Action {action_id} reported as {status}: {result}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logging.error(f"Report action result failed: {e}")
        return jsonify({"error": str(e)}), 500
```

---

### Phase 4.3: Agent Handler (3 hours) 🔴 CRITICAL

**File:** `fleet_agent.py`

**Add imports:**
```python
import ctypes  # For Windows msgbox
import subprocess
import platform
import os
import sys
```

**Add functions:**

```python
def get_pending_actions(server: str, token: str, machine_id: str) -> list:
    """Poll for pending actions."""
    url = f"{server.rstrip('/')}/api/actions/pending?machine_id={machine_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("actions", [])
    except Exception as e:
        logging.debug(f"Get pending actions failed: {e}")
        return []


def execute_action(action: dict) -> tuple[bool, str]:
    """Execute an action and return (success, result_message)."""
    action_type = action.get("type")
    data = action.get("data", {})
    
    if action_type == "message":
        message = data.get("message", "No message")
        title = data.get("title", "DashFleet")
        return execute_message(message, title)
    
    elif action_type == "restart":
        return execute_restart()
    
    elif action_type == "reboot":
        return execute_reboot()
    
    else:
        return False, f"Unknown action type: {action_type}"


def execute_message(message: str, title: str = "DashFleet") -> tuple[bool, str]:
    """Display a message box (OS-specific)."""
    try:
        if platform.system() == "Windows":
            ctypes.windll.user32.MessageBoxW(
                0, message, title, 
                0x1000 | 0x40  # MB_SYSTEMMODAL | MB_ICONINFORMATION
            )
            return True, "Message displayed (Windows)"
        
        elif platform.system() == "Linux":
            try:
                subprocess.run(
                    ["notify-send", title, message],
                    timeout=5,
                    capture_output=True
                )
                return True, "Notification sent (notify-send)"
            except:
                try:
                    subprocess.run(
                        ["zenity", "--info", "--title", title, "--text", message],
                        timeout=5,
                        capture_output=True
                    )
                    return True, "Dialog shown (zenity)"
                except:
                    return False, "No notification system found (install notify-send or zenity)"
        
        elif platform.system() == "Darwin":  # macOS
            try:
                cmd = f'osascript -e \'display notification "{message}" with title "{title}\"\''
                os.system(cmd)
                return True, "Notification sent (macOS)"
            except Exception as e:
                return False, str(e)
        
        else:
            return False, f"Unsupported OS: {platform.system()}"
    
    except Exception as e:
        return False, f"Message execution failed: {str(e)}"


def execute_restart() -> tuple[bool, str]:
    """Restart the agent process."""
    try:
        logging.info("Restarting agent...")
        os.execvp(sys.executable, [sys.executable] + sys.argv)
        return True, "Agent restarted"
    except Exception as e:
        return False, f"Restart failed: {str(e)}"


def execute_reboot() -> tuple[bool, str]:
    """Reboot the machine."""
    try:
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "60"], check=True)
            return True, "Reboot scheduled (60 seconds)"
        else:
            subprocess.run(["sudo", "shutdown", "-r", "+1"], check=True)
            return True, "Reboot scheduled (1 minute)"
    except Exception as e:
        return False, f"Reboot command failed: {str(e)}"


def report_action_result(server: str, token: str, action_id: str, 
                        status: str, result: str) -> bool:
    """Report action execution result to server."""
    url = f"{server.rstrip('/')}/api/actions/report"
    payload = {
        "action_id": action_id,
        "status": status,
        "result": result
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}"
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.getcode() < 300
    except Exception as e:
        logging.error(f"Report action result failed: {e}")
        return False
```

**Modify main loop:**

```python
# In main() function, modify the while loop:

action_poll_counter = 0
while True:
    # Collect and report metrics (existing code)
    report = collect_agent_stats()
    ok, msg = post_report(url, token, machine_id, report)
    
    # ... heartbeat code ...
    
    # Poll for actions every 30 seconds (or every 3rd cycle if interval=10s)
    action_poll_counter += 1
    if action_poll_counter >= 3:
        actions = get_pending_actions(server, token, machine_id)
        for action in actions:
            action_id = action.get("action_id")
            try:
                success, result = execute_action(action)
                status = "done" if success else "error"
                report_action_result(server, token, action_id, status, result)
                log_line(f"[{time.strftime('%H:%M:%S')}] Action {action_id} executed: {result}")
            except Exception as e:
                log_line(f"[{time.strftime('%H:%M:%S')}] Action {action_id} failed: {e}")
                report_action_result(server, token, action_id, "error", str(e))
        
        action_poll_counter = 0
    
    time.sleep(max(1.0, interval))
```

---

### Phase 4.4: Dashboard UI (2 hours) 🟠 IMPORTANT

**File:** `templates/fleet.html`

**Add action button to machine cards:**

```html
<!-- In renderFleet() function, add button after health score display -->
<div class="card-actions">
  <button class="action-btn" onclick="showActionModal('${machine.id}', '${machine.machine_id}')" 
          title="Send message or command">
    📨 Actions
  </button>
</div>
```

**Add modal HTML (at end of page, before closing main tag):**

```html
<!-- Action Modal -->
<div id="action-modal" class="modal" style="display:none;">
  <div class="modal-content">
    <div class="modal-header">
      <h3 id="action-modal-title">Send Action</h3>
      <button class="modal-close" onclick="closeActionModal()">×</button>
    </div>
    
    <div class="modal-body">
      <div class="form-group">
        <label for="action-type">Action Type:</label>
        <select id="action-type" onchange="updateActionForm()">
          <option value="message">💬 Send Message</option>
          <option value="restart">🔄 Restart Agent</option>
          <option value="reboot">🔌 Reboot Machine</option>
        </select>
      </div>
      
      <div id="message-form" class="form-group" style="display:none;">
        <label for="action-message">Message:</label>
        <textarea id="action-message" placeholder="Enter message..." rows="3"></textarea>
      </div>
      
      <div id="reboot-warning" class="alert" style="display:none;">
        ⚠️ This will reboot the machine!
      </div>
    </div>
    
    <div class="modal-footer">
      <button class="btn-primary" onclick="sendAction()">Send</button>
      <button class="btn-secondary" onclick="closeActionModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Action Results Display -->
<div id="action-results" class="action-results" style="display:none;">
  <h4>Action Results:</h4>
  <div id="results-list"></div>
</div>
```

**Add CSS styling:**

```css
.card-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 8px 12px;
  background: var(--accent, #007bff);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.action-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-secondary, #fff);
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border, #ccc);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary, #666);
}

.modal-body {
  padding: 16px;
}

.modal-footer {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid var(--border, #ccc);
}

.btn-primary {
  flex: 1;
  padding: 10px;
  background: var(--accent, #007bff);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-secondary {
  flex: 1;
  padding: 10px;
  background: var(--bg-tertiary, #f0f0f0);
  border: 1px solid var(--border, #ccc);
  border-radius: 4px;
  cursor: pointer;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
  font-size: 13px;
}

.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border, #ccc);
  border-radius: 4px;
  font-family: inherit;
}

.alert {
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  color: #856404;
  font-size: 13px;
}
```

**Add JavaScript functions:**

```javascript
let currentMachineId = null;

function showActionModal(machineId, machineName) {
  currentMachineId = machineId;
  document.getElementById('action-modal-title').textContent = `Actions for ${machineName}`;
  document.getElementById('action-modal').style.display = 'flex';
  updateActionForm();
}

function closeActionModal() {
  document.getElementById('action-modal').style.display = 'none';
  currentMachineId = null;
}

function updateActionForm() {
  const actionType = document.getElementById('action-type').value;
  document.getElementById('message-form').style.display = 
    actionType === 'message' ? 'block' : 'none';
  document.getElementById('reboot-warning').style.display = 
    actionType === 'reboot' ? 'block' : 'none';
}

function sendAction() {
  const machineId = currentMachineId;
  const actionType = document.getElementById('action-type').value;
  
  const data = {
    machine_id: machineId,
    action_type: actionType,
    data: {}
  };
  
  if (actionType === 'message') {
    data.data.message = document.getElementById('action-message').value;
    data.data.title = 'DashFleet';
    if (!data.data.message) {
      showToast('Please enter a message', 'error');
      return;
    }
  }
  
  fetch('/api/actions/queue', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify(data)
  })
  .then(r => r.json())
  .then(d => {
    if (d.ok || d.action_id) {
      showToast(`Action sent to ${machineId}!`, 'success');
      closeActionModal();
    } else {
      showToast('Error: ' + (d.error || 'Unknown error'), 'error');
    }
  })
  .catch(e => showToast('Error: ' + e, 'error'));
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
  const modal = document.getElementById('action-modal');
  if (e.target === modal) {
    closeActionModal();
  }
});
```

---

## 🔄 Implementation Checklist

### Database (Phase 4.1)
- [ ] Create migration script `scripts/init_actions_table.py`
- [ ] Run locally to test schema
- [ ] Add SQL to documentation

### API Endpoints (Phase 4.2)
- [ ] Add imports for sqlite3, json to main.py
- [ ] Add `/api/actions/queue` endpoint
- [ ] Add `/api/actions/pending` endpoint
- [ ] Add `/api/actions/report` endpoint
- [ ] Test all endpoints with curl

### Agent Handler (Phase 4.3)
- [ ] Add imports (ctypes, subprocess, platform, os, sys)
- [ ] Add `get_pending_actions()` function
- [ ] Add `execute_action()` dispatcher
- [ ] Add `execute_message()` function
- [ ] Add `execute_restart()` function
- [ ] Add `execute_reboot()` function
- [ ] Add `report_action_result()` function
- [ ] Modify main loop for action polling
- [ ] Test locally with message action

### Dashboard UI (Phase 4.4)
- [ ] Add action button to card rendering
- [ ] Add modal HTML
- [ ] Add CSS styling
- [ ] Add JavaScript functions
- [ ] Test modal display
- [ ] Test action sending

### Documentation
- [ ] Update README with usage examples
- [ ] Add API documentation for new endpoints
- [ ] Create troubleshooting guide

---

## 🧪 Testing Strategy

### Local Testing
```bash
# 1. Initialize database
python scripts/init_actions_table.py

# 2. Start API server
python main.py --web

# 3. In new terminal, start agent
python fleet_agent.py --server http://localhost:5000 \
  --token test_token --machine-id test-pc --interval 5

# 4. Test via curl
curl -X POST http://localhost:5000/api/actions/queue \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "test-pc",
    "action_type": "message",
    "data": {"message": "Hello from DashFleet!", "title": "Test"}
  }'

# 5. Watch agent logs for message execution
```

### Browser Testing
1. Open http://localhost:5000/fleet
2. Click "📨 Actions" on a machine
3. Select "Send Message"
4. Enter message and click "Send"
5. Watch agent window for message box

---

## ⏱️ Timeline

| Step | Component | Time | Status |
|------|-----------|------|--------|
| 1 | DB Schema | 30min | Not started |
| 2 | API Endpoints | 2h | Not started |
| 3 | Agent Handler | 3h | Not started |
| 4 | Dashboard UI | 2h | Not started |
| 5 | Testing & Docs | 1h | Not started |
| **Total** | | **8.5h** | |

---

## 📝 Notes

- **Backward Compatible:** Existing agents unaffected (action polling optional)
- **Polling-based:** No need for reverse connections/webhooks
- **OS-specific:** Message display adapted for Windows/Linux/macOS
- **Simple first:** Start with message action, expand to restart/reboot later

---

**Ready to start Phase 4? Let's go!** 🚀

