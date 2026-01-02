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
    # Update in-memory state
    fleet_state[store_key] = {
        'id': machine_id,  # Explicit id for frontend display
        'machine_id': machine_id,
        'report': report,
        'ts': now_ts,
        'client': client_ip,
        'org_id': org_id
    }

    # Persist to disk (best-effort)
    save_fn()

    # Persist to SQLite
    try:
        conn = sqlite3.connect('data/fleet.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO fleet (id, report, ts, client, org_id) VALUES (?, ?, ?, ?, ?)',
            (store_key, json.dumps(report), now_ts, client_ip, org_id)
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
