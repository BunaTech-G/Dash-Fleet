"""
Database utility functions for fleet data persistence.
Handles SQLite operations for fleet reporting.
"""

import sqlite3
import json
import logging


def insert_fleet_report(
    store_key: str,
    machine_id: str,
    report: dict,
    now_ts: float,
    client_ip: str,
    org_id: str,
    fleet_state: dict,
    save_fn: callable
):
    """
    Insert or update a fleet report in both memory and SQLite.

    Args:
        store_key: Composite key "org_id:machine_id"
        machine_id: Machine identifier
        report: Metrics dictionary
        now_ts: Current timestamp
        client_ip: Client IP address
        org_id: Organization ID
        fleet_state: In-memory fleet state dictionary
        save_fn: Function to save fleet state to disk
    """
    # Extract system info from report
    system_info = report.get('system', {})
    os_name = system_info.get('os', 'N/A')
    os_version = system_info.get('os_version', '')
    architecture = system_info.get('architecture', 'N/A')
    python_version = system_info.get('python_version', 'N/A')
    hardware_id = system_info.get('hardware_id', 'N/A')
    
    # Combine OS name and version
    full_os = f"{os_name} {os_version}" if os_version else os_name
    
    # Update in-memory state
    fleet_state[store_key] = {
        'id': machine_id,
        'machine_id': machine_id,
        'report': report,
        'ts': now_ts,
        'client': client_ip,
        'org_id': org_id,
        'os': full_os,
        'architecture': architecture,
        'python_version': python_version,
        'hardware_id': hardware_id,
        'status': 'ONLINE'
    }

    # Persist to disk (best-effort)
    save_fn()

    # Persist to SQLite with system info
    try:
        conn = sqlite3.connect('data/fleet.db')
        cursor = conn.cursor()
        
        # Check if machine exists
        cursor.execute('SELECT deleted_at FROM fleet WHERE id = ?', (store_key,))
        existing = cursor.fetchone()
        
        # If machine was deleted, restore it
        if existing and existing[0] is not None:
            cursor.execute(
                'UPDATE fleet SET report = ?, ts = ?, client = ?, os = ?, architecture = ?, python_version = ?, hardware_id = ?, status = ?, deleted_at = NULL WHERE id = ?',
                (json.dumps(report), now_ts, client_ip, full_os, architecture, python_version, hardware_id, 'ONLINE', store_key)
            )
        else:
            cursor.execute(
                'INSERT OR REPLACE INTO fleet (id, report, ts, client, org_id, os, architecture, python_version, hardware_id, status, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)',
                (store_key, json.dumps(report), now_ts, client_ip, org_id, full_os, architecture, python_version, hardware_id, 'ONLINE')
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f'Database insert error: {e}')


def _save_fleet_state(fleet_state: dict, state_path: str):
    """
    Save fleet state to JSON file.

    Args:
        fleet_state: In-memory fleet state dictionary
        state_path: Path to JSON file
    """
    try:
        import json
        from pathlib import Path
        Path(state_path).parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w') as f:
            json.dump(fleet_state, f, indent=2)
    except Exception as e:
        logging.error(f'Failed to save fleet state: {e}')
