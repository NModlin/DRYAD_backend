
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from dryad.main import app
    from dryad.core.guardian import Guardian
    from dryad.services.memory_guild.coordinator import MemoryCoordinator
    from dryad.services.content.engine import ContentCreationEngine
    print("Imports: OK")
except Exception as e:
    print(f"Imports: FAILED - {e}")
    sys.exit(1)

async def check_systems():
    print("Checking Systems...")
    
    # Check 1: Guardian
    try:
        g = Guardian()
        print("Guardian Instantiation: OK")
    except Exception as e:
        print(f"Guardian Instantiation: FAILED - {e}")

    # Check 2: Memory Guild
    try:
        m = MemoryCoordinator()
        print("Memory Guild Instantiation: OK")
    except Exception as e:
        print(f"Memory Guild Instantiation: FAILED - {e}")

    # Check 3: Content Engine
    try:
        c = ContentCreationEngine()
        print("Content Engine Instantiation: OK")
    except Exception as e:
        print(f"Content Engine Instantiation: FAILED - {e}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    asyncio.run(check_systems())
