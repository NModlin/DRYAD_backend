"""
Seed Dryad Data Script

Creates sample data for testing Dryad API endpoints:
- Creates 2 groves
- Creates 5 branches (with parent-child relationships)
- Creates 3 vessels
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.dryad.services.grove_service import GroveService
from app.dryad.services.branch_service import BranchService
from app.dryad.services.vessel_service import VesselService
from app.dryad.schemas.grove_schemas import GroveCreate
from app.dryad.schemas.branch_schemas import BranchCreate
from app.dryad.schemas.vessel_schemas import VesselCreate


async def seed_dryad_data():
    """Seed Dryad database with sample data."""
    
    print("🌳 Starting Dryad data seeding...")
    
    # Get database session
    async for db in get_db():
        try:
            # Initialize services
            grove_service = GroveService(db)
            branch_service = BranchService(db)
            vessel_service = VesselService(db)
            
            # Create Groves
            print("\n📁 Creating groves...")
            
            grove1_data = GroveCreate(
                name="AI Research Grove",
                description="Exploring artificial intelligence and machine learning concepts",
                template_metadata={"category": "research", "tags": ["AI", "ML", "Deep Learning"]},
                is_favorite=True
            )
            grove1 = await grove_service.create_grove(grove1_data)
            print(f"  ✓ Created grove: {grove1.name} (ID: {grove1.id})")
            
            grove2_data = GroveCreate(
                name="Quantum Computing Grove",
                description="Investigating quantum computing principles and applications",
                template_metadata={"category": "research", "tags": ["Quantum", "Physics"]},
                is_favorite=False
            )
            grove2 = await grove_service.create_grove(grove2_data)
            print(f"  ✓ Created grove: {grove2.name} (ID: {grove2.id})")
            
            # Create Branches for Grove 1
            print("\n🌿 Creating branches...")
            
            # Root branch
            branch1_data = BranchCreate(
                grove_id=grove1.id,
                name="Neural Networks Fundamentals",
                description="Exploring the basics of neural networks",
                priority="high"
            )
            branch1 = await branch_service.create_branch(branch1_data)
            print(f"  ✓ Created branch: {branch1.name} (ID: {branch1.id})")

            # Child branches
            branch2_data = BranchCreate(
                grove_id=grove1.id,
                parent_id=branch1.id,
                name="Convolutional Neural Networks",
                description="Deep dive into CNNs for image processing",
                priority="medium"
            )
            branch2 = await branch_service.create_branch(branch2_data)
            print(f"  ✓ Created branch: {branch2.name} (ID: {branch2.id})")

            branch3_data = BranchCreate(
                grove_id=grove1.id,
                parent_id=branch1.id,
                name="Recurrent Neural Networks",
                description="Exploring RNNs for sequence data",
                priority="medium"
            )
            branch3 = await branch_service.create_branch(branch3_data)
            print(f"  ✓ Created branch: {branch3.name} (ID: {branch3.id})")

            # Create Branches for Grove 2
            branch4_data = BranchCreate(
                grove_id=grove2.id,
                name="Quantum Superposition",
                description="Understanding quantum superposition principles",
                priority="high"
            )
            branch4 = await branch_service.create_branch(branch4_data)
            print(f"  ✓ Created branch: {branch4.name} (ID: {branch4.id})")

            branch5_data = BranchCreate(
                grove_id=grove2.id,
                parent_id=branch4.id,
                name="Quantum Entanglement",
                description="Exploring quantum entanglement phenomena",
                priority="medium"
            )
            branch5 = await branch_service.create_branch(branch5_data)
            print(f"  ✓ Created branch: {branch5.name} (ID: {branch5.id})")
            
            # Create Vessels
            print("\n🏺 Creating vessels...")
            
            vessel1_data = VesselCreate(
                branch_id=branch1.id,
                initial_context="Initial exploration of neural network architectures and training methods"
            )
            vessel1 = await vessel_service.create_vessel(vessel1_data)
            print(f"  ✓ Created vessel for branch: {branch1.name} (ID: {vessel1.id})")
            
            vessel2_data = VesselCreate(
                branch_id=branch2.id,
                parent_branch_id=branch1.id,
                initial_context="Investigating CNN architectures like ResNet, VGG, and Inception"
            )
            vessel2 = await vessel_service.create_vessel(vessel2_data)
            print(f"  ✓ Created vessel for branch: {branch2.name} (ID: {vessel2.id})")
            
            vessel3_data = VesselCreate(
                branch_id=branch4.id,
                initial_context="Exploring quantum superposition and its implications for quantum computing"
            )
            vessel3 = await vessel_service.create_vessel(vessel3_data)
            print(f"  ✓ Created vessel for branch: {branch4.name} (ID: {vessel3.id})")
            
            # Summary
            print("\n" + "="*60)
            print("✅ Dryad data seeding complete!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"  • Groves created: 2")
            print(f"  • Branches created: 5")
            print(f"  • Vessels created: 3")
            print(f"\n🔗 Grove IDs:")
            print(f"  • {grove1.name}: {grove1.id}")
            print(f"  • {grove2.name}: {grove2.id}")
            print(f"\n🌿 Branch IDs:")
            print(f"  • {branch1.name}: {branch1.id}")
            print(f"  • {branch2.name}: {branch2.id}")
            print(f"  • {branch3.name}: {branch3.id}")
            print(f"  • {branch4.name}: {branch4.id}")
            print(f"  • {branch5.name}: {branch5.id}")
            print(f"\n🏺 Vessel IDs:")
            print(f"  • Vessel 1: {vessel1.id}")
            print(f"  • Vessel 2: {vessel2.id}")
            print(f"  • Vessel 3: {vessel3.id}")
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"\n❌ Error seeding data: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            break  # Exit the async generator


if __name__ == "__main__":
    asyncio.run(seed_dryad_data())

