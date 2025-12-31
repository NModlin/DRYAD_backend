"""
Script to run Alembic migrations programmatically
"""
import sys
import os
from alembic.config import Config
from alembic import command

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create Alembic config
alembic_cfg = Config(os.path.join(script_dir, "alembic.ini"))

# Set the script location
alembic_cfg.set_main_option("script_location", os.path.join(script_dir, "alembic"))

def upgrade():
    """Run all migrations to head"""
    print("Running migrations to head...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

def downgrade(revision="-1"):
    """Downgrade by one revision or to specific revision"""
    print(f"Downgrading to {revision}...")
    try:
        command.downgrade(alembic_cfg, revision)
        print("✅ Downgrade completed successfully!")
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        sys.exit(1)

def current():
    """Show current revision"""
    print("Current revision:")
    try:
        command.current(alembic_cfg)
    except Exception as e:
        print(f"❌ Failed to get current revision: {e}")
        sys.exit(1)

def history():
    """Show migration history"""
    print("Migration history:")
    try:
        command.history(alembic_cfg)
    except Exception as e:
        print(f"❌ Failed to get history: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py [upgrade|downgrade|current|history]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "upgrade":
        upgrade()
    elif action == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        downgrade(revision)
    elif action == "current":
        current()
    elif action == "history":
        history()
    else:
        print(f"Unknown action: {action}")
        print("Valid actions: upgrade, downgrade, current, history")
        sys.exit(1)

