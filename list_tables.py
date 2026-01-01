import sqlite3

db_path = "data/fleet.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("Tables dans la base :", tables)
conn.close()
