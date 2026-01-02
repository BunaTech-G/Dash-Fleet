#!/usr/bin/env python3
"""Initialize actions table for Phase 4 message/action system."""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/fleet.db")


def init_actions_table():
    """Create actions table and indexes."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print("Creating actions table...")
    cursor.execute('''
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
        )
    ''')
    
    print("Creating index for agent polling...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_actions_pending 
        ON actions(machine_id, org_id, status)
    ''')
    
    print("Creating index for recent actions...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_actions_recent 
        ON actions(created_at DESC)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Actions table initialized successfully!")
    print(f"   Database: {DB_PATH}")
    print(f"   Table: actions")
    print(f"   Indexes: idx_actions_pending, idx_actions_recent")


if __name__ == "__main__":
    try:
        init_actions_table()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
