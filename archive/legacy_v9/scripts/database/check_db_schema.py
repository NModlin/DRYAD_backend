"""
Script to check database schema and verify Dryad tables
"""
import sqlite3
import os

db_path = "data/DRYAD.AI.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
    exit(1)

print(f"✅ Database found at {db_path}")
print("\n" + "="*60)
print("CURRENT DATABASE TABLES")
print("="*60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print(f"\nTotal tables: {len(tables)}\n")

dryad_tables = []
other_tables = []

for table in tables:
    table_name = table[0]
    if table_name.startswith('dryad_'):
        dryad_tables.append(table_name)
    else:
        other_tables.append(table_name)

print("📊 Dryad Tables:")
if dryad_tables:
    for table in dryad_tables:
        print(f"  ✅ {table}")
else:
    print("  ❌ No Dryad tables found")

print(f"\n📊 Other Tables ({len(other_tables)}):")
for table in other_tables:
    print(f"  - {table}")

# Check alembic version
print("\n" + "="*60)
print("ALEMBIC MIGRATION STATUS")
print("="*60)

try:
    cursor.execute("SELECT version_num FROM alembic_version;")
    version = cursor.fetchone()
    if version:
        print(f"✅ Current migration version: {version[0]}")
    else:
        print("❌ No migration version found")
except sqlite3.OperationalError:
    print("❌ alembic_version table not found - database not initialized")

conn.close()

print("\n" + "="*60)
print("EXPECTED DRYAD TABLES")
print("="*60)

expected_tables = [
    "dryad_groves",
    "dryad_branches",
    "dryad_vessels",
    "dryad_dialogues",
    "dryad_dialogue_messages",
    "dryad_observation_points",
    "dryad_possibilities"
]

print("\nExpected Dryad tables:")
for table in expected_tables:
    status = "✅" if table in dryad_tables else "❌"
    print(f"  {status} {table}")

missing_count = len([t for t in expected_tables if t not in dryad_tables])
if missing_count == 0:
    print("\n🎉 All Dryad tables are present!")
else:
    print(f"\n⚠️  {missing_count} Dryad table(s) missing - migration needed")

