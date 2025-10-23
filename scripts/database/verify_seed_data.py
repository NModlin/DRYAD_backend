"""
Verify seed data was created successfully
"""
import sqlite3
import json

DB_PATH = "data/DRYAD.AI.db"

def verify_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔍 Verifying Dryad seed data...")
    print("=" * 60)
    
    # Check groves
    cursor.execute("SELECT COUNT(*), name FROM dryad_groves GROUP BY name")
    groves = cursor.fetchall()
    print(f"\n📊 Groves ({len(groves)} total):")
    for count, name in groves:
        print(f"  ✅ {name}")
    
    # Check branches
    cursor.execute("SELECT COUNT(*) FROM dryad_branches")
    branch_count = cursor.fetchone()[0]
    print(f"\n🌳 Branches: {branch_count} total")
    
    # Show tree structure
    cursor.execute("""
        SELECT b.name, b.path_depth, b.status, g.name as grove_name
        FROM dryad_branches b
        JOIN dryad_groves g ON b.grove_id = g.id
        ORDER BY g.name, b.path_depth, b.name
    """)
    branches = cursor.fetchall()
    current_grove = None
    for name, depth, status, grove_name in branches:
        if grove_name != current_grove:
            print(f"\n  Grove: {grove_name}")
            current_grove = grove_name
        indent = "  " * (depth + 1)
        print(f"{indent}└─ {name} (depth={depth}, status={status})")
    
    # Check observation points
    cursor.execute("SELECT COUNT(*), name FROM dryad_observation_points GROUP BY name")
    obs_points = cursor.fetchall()
    print(f"\n🔍 Observation Points ({len(obs_points)} total):")
    for count, name in obs_points:
        print(f"  ✅ {name}")
    
    # Check possibilities
    cursor.execute("SELECT COUNT(*) FROM dryad_possibilities")
    poss_count = cursor.fetchone()[0]
    print(f"\n🔀 Possibilities: {poss_count} total")
    
    # Check vessels
    cursor.execute("SELECT COUNT(*) FROM dryad_vessels")
    vessel_count = cursor.fetchone()[0]
    print(f"\n📦 Vessels: {vessel_count} total")
    
    # Check dialogues
    cursor.execute("SELECT COUNT(*) FROM dryad_dialogues")
    dialogue_count = cursor.fetchone()[0]
    print(f"\n💬 Dialogues: {dialogue_count} total")
    
    # Check dialogue messages
    cursor.execute("SELECT COUNT(*), role FROM dryad_dialogue_messages GROUP BY role")
    messages = cursor.fetchall()
    print(f"\n💬 Dialogue Messages:")
    for count, role in messages:
        print(f"  - {role}: {count} messages")
    
    print("\n" + "=" * 60)
    print("✅ Seed data verification complete!")
    
    conn.close()


if __name__ == "__main__":
    verify_data()

