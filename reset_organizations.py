import sqlite3
from pathlib import Path

DB_PATH = Path("data/fleet.db")

def reset_organizations_table():
    if not DB_PATH.exists():
        print("Aucune base de données trouvée.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM organizations")
        conn.commit()
        print("Table organizations vidée avec succès.")
    except Exception as e:
        print(f"Erreur lors de la suppression : {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_organizations_table()
