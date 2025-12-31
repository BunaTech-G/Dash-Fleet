"""
Utilitaires de gestion de la base de données pour Mini-MDM (extraction logique métier).
"""
import sqlite3
from pathlib import Path
import time

FLEET_DB_PATH = Path("data/fleet.db")


def insert_organization(org_id: str, name: str, key: str) -> bool:
    try:
        conn = sqlite3.connect(str(FLEET_DB_PATH))
        cur = conn.cursor()
        sql_org = 'INSERT INTO organizations (id, name) VALUES (?, ?)'
        cur.execute(sql_org, (org_id, name))
        sql_key = (
            'INSERT INTO api_keys (key, org_id, created_at, revoked) '
            'VALUES (?, ?, ?, 0)'
        )
        cur.execute(sql_key, (key, org_id, time.time()))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def insert_fleet_report(store_key: str, machine_id: str, report: dict, now_ts: float, client: str, org_id: str, FLEET_STATE: dict, save_func) -> None:
    FLEET_STATE[store_key] = {
        "id": machine_id,
        "report": report,
        "ts": now_ts,
        "client": client,
        "org_id": org_id,
    }
    save_func()
