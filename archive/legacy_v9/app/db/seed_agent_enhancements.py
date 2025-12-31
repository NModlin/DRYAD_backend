"""
Seed Agent Enhancements

Seeds default data for the four agent enhancements:
1. Tool catalog
2. Collaboration patterns
3. Guardrail configurations
4. Approval policies
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.agent_tools import (
    AgentToolCatalog, ToolCategory, ToolSecurityLevel,
    get_default_tool_catalog
)
from app.models.agent_collaboration import (
    CollaborationPattern, get_default_collaboration_patterns
)
from app.models.execution_guardrails import (
    GuardrailConfiguration, get_default_guardrail_configs
)
from app.models.hitl_approval import (
    ApprovalPolicy, get_default_approval_policies
)


def seed_tool_catalog(db: Session):
    """Seed default tools into the catalog."""
    print("🔧 Seeding tool catalog...")
    
    default_tools = get_default_tool_catalog()
    count = 0
    
    for tool_data in default_tools:
        # Check if tool already exists
        existing = db.query(AgentToolCatalog).filter(
            AgentToolCatalog.tool_id == tool_data["tool_id"]
        ).first()
        
        if not existing:
            tool = AgentToolCatalog(
                id=uuid.uuid4(),
                **tool_data
            )
            db.add(tool)
            count += 1
            print(f"  ✓ Added tool: {tool_data['tool_id']}")
    
    db.commit()
    print(f"✅ Seeded {count} tools\n")


def seed_collaboration_patterns(db: Session):
    """Seed default collaboration patterns."""
    print("🤝 Seeding collaboration patterns...")
    
    default_patterns = get_default_collaboration_patterns()
    count = 0
    
    for pattern_data in default_patterns:
        # Check if pattern already exists
        existing = db.query(CollaborationPattern).filter(
            CollaborationPattern.pattern_id == pattern_data["pattern_id"]
        ).first()
        
        if not existing:
            pattern = CollaborationPattern(
                id=uuid.uuid4(),
                **pattern_data
            )
            db.add(pattern)
            count += 1
            print(f"  ✓ Added pattern: {pattern_data['pattern_id']}")
    
    db.commit()
    print(f"✅ Seeded {count} collaboration patterns\n")


def seed_guardrail_configurations(db: Session):
    """Seed default guardrail configurations."""
    print("🛡️ Seeding guardrail configurations...")
    
    default_configs = get_default_guardrail_configs()
    count = 0
    
    for config_data in default_configs:
        # Check if config already exists
        existing = db.query(GuardrailConfiguration).filter(
            GuardrailConfiguration.config_id == config_data["config_id"]
        ).first()
        
        if not existing:
            config = GuardrailConfiguration(
                id=uuid.uuid4(),
                **config_data
            )
            db.add(config)
            count += 1
            print(f"  ✓ Added guardrail: {config_data['config_id']}")
    
    db.commit()
    print(f"✅ Seeded {count} guardrail configurations\n")


def seed_approval_policies(db: Session):
    """Seed default approval policies."""
    print("👤 Seeding approval policies...")
    
    default_policies = get_default_approval_policies()
    count = 0
    
    for policy_data in default_policies:
        # Check if policy already exists
        existing = db.query(ApprovalPolicy).filter(
            ApprovalPolicy.policy_id == policy_data["policy_id"]
        ).first()
        
        if not existing:
            policy = ApprovalPolicy(
                id=uuid.uuid4(),
                **policy_data
            )
            db.add(policy)
            count += 1
            print(f"  ✓ Added policy: {policy_data['policy_id']}")
    
    db.commit()
    print(f"✅ Seeded {count} approval policies\n")


def seed_all_enhancements(db: Session):
    """Seed all agent enhancement default data."""
    print("\n" + "="*60)
    print("🌱 SEEDING AGENT ENHANCEMENTS")
    print("="*60 + "\n")
    
    try:
        seed_tool_catalog(db)
        seed_collaboration_patterns(db)
        seed_guardrail_configurations(db)
        seed_approval_policies(db)
        
        print("="*60)
        print("✅ ALL AGENT ENHANCEMENTS SEEDED SUCCESSFULLY!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    # For standalone execution
    from app.database.database import SessionLocal

    db = SessionLocal()
    try:
        seed_all_enhancements(db)
    finally:
        db.close()

