import sqlite3
from datetime import datetime
import secrets

# Génère un token admin sécurisé
admin_token = secrets.token_hex(24)
db_path = "data/fleet.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute(
    "INSERT INTO tokens (token, type, created_at) VALUES (?, 'action', ?)",
    (admin_token, int(datetime.now().timestamp()))
)
conn.commit()
conn.close()
print("ACTION_TOKEN inséré :", admin_token)
