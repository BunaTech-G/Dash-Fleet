#!/usr/bin/env python3
"""Update fleet database schema with new columns."""
import sqlite3

conn = sqlite3.connect('data/fleet.db')
c = conn.cursor()

columns_to_add = [
    ('os', 'TEXT DEFAULT "N/A"'),
    ('architecture', 'TEXT DEFAULT "N/A"'),
    ('python_version', 'TEXT DEFAULT "N/A"'),
    ('hardware_id', 'TEXT DEFAULT "N/A"'),
    ('status', 'TEXT DEFAULT "ONLINE"'),
    ('deleted_at', 'REAL DEFAULT NULL'),
]

for col_name, col_type in columns_to_add:
    try:
        c.execute(f'ALTER TABLE fleet ADD COLUMN {col_name} {col_type}')
        print(f'✓ Column {col_name} added')
    except sqlite3.OperationalError:
        print(f'Column {col_name} already exists')

conn.commit()
conn.close()
print('\n✅ Database schema updated successfully')
