import sqlite3

conn = sqlite3.connect('data/DRYAD.AI.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "dryad%"')
tables = [row[0] for row in cursor.fetchall()]
print(f"Dryad tables: {tables}")
conn.close()

