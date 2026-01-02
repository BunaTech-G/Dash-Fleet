import sqlite3
conn = sqlite3.connect('data/fleet.db')
cursor = conn.cursor()
cursor.execute('SELECT key, org_id FROM api_keys WHERE revoked=0 LIMIT 1')
result = cursor.fetchone()
if result:
    print(f'API_KEY={result[0]}')
    print(f'ORG_ID={result[1]}')
else:
    print('NO_KEY_FOUND')
conn.close()
