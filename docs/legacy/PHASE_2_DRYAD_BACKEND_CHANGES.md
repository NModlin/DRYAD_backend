# Phase 2: DRYAD_backend File Changes

**Phase**: Specialization & Skill Trees  
**Component**: DRYAD_backend  
**Date**: October 23, 2025

---

## 📁 Files to Create (14 new files)

### Models (4 files)

#### 1. `app/models/specialization.py`
```python
"""
Specialization profile model for agents.
Defines primary/secondary specializations, levels, and configuration.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class SpecializationProfile(Base):
    __tablename__ = "specialization_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, unique=True, index=True)
    
    # Primary specialization
    primary_specialization = Column(String, nullable=False)  # memetics, warfare_studies, etc.
    specialization_level = Column(Integer, nullable=False, default=1)  # 1-10
    
    # Secondary specializations
    secondary_specializations = Column(JSON, default=list)  # ["data_science", "philosophy"]
    
    # Configuration
    specialization_tools = Column(JSON, default=list)  # Tool IDs
    specialization_curriculum = Column(String, nullable=True)  # Curriculum ID
    specialization_constraints = Column(JSON, default=dict)  # Custom constraints
    
    # Cross-specialization
    cross_specialization_enabled = Column(Boolean, default=True)
    cross_specialization_penalty = Column(Float, default=0.2)  # 0.0-1.0
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, onupdate="CURRENT_TIMESTAMP")
    
    # Relationships
    agent = relationship("Agent", back_populates="specialization_profile")
```

#### 2. `app/models/skill_tree.py`
```python
"""
Skill tree and skill node models.
Defines skill trees, nodes, prerequisites, and bonuses.
"""

from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class SkillTree(Base):
    __tablename__ = "skill_trees"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Specialization
    specialization = Column(String, nullable=False, index=True)
    
    # Customization
    is_custom = Column(Boolean, default=False)
    creator_id = Column(String, nullable=True, index=True)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, onupdate="CURRENT_TIMESTAMP")
    
    # Relationships
    skill_nodes = relationship("SkillNode", back_populates="skill_tree", cascade="all, delete-orphan")
    progression_paths = relationship("ProgressionPath", back_populates="skill_tree", cascade="all, delete-orphan")

class SkillNode(Base):
    __tablename__ = "skill_nodes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_tree_id = Column(String, ForeignKey("skill_trees.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Progression
    max_level = Column(Integer, nullable=False, default=5)
    experience_per_level = Column(Integer, nullable=False, default=100)
    
    # Dependencies
    prerequisites = Column(JSON, default=list)  # ["skill_node_1", "skill_node_2"]
    
    # Bonuses
    capability_bonuses = Column(JSON, default=dict)  # {"reasoning": 0.1}
    personality_shifts = Column(JSON, default=dict)  # {"analytical": 0.05}
    
    # Unlocks
    unlocks_tools = Column(JSON, default=list)  # ["tool_id_1"]
    unlocks_competitions = Column(JSON, default=list)  # ["competition_id_1"]
    
    # Position (for visualization)
    tree_position_x = Column(Integer, nullable=True)
    tree_position_y = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, onupdate="CURRENT_TIMESTAMP")
    
    # Relationships
    skill_tree = relationship("SkillTree", back_populates="skill_nodes")
    agent_progress = relationship("AgentSkillProgress", back_populates="skill_node", cascade="all, delete-orphan")
```

#### 3. `app/models/skill_progress.py`
```python
"""
Agent skill progress tracking model.
Tracks individual agent progress through skill nodes.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class AgentSkillProgress(Base):
    __tablename__ = "agent_skill_progress"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    skill_node_id = Column(String, ForeignKey("skill_nodes.id"), nullable=False, index=True)
    
    # Progress
    current_level = Column(Integer, nullable=False, default=0)
    current_experience = Column(Integer, nullable=False, default=0)
    
    # Status
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(TIMESTAMP, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, onupdate="CURRENT_TIMESTAMP")
    
    # Relationships
    agent = relationship("Agent", back_populates="skill_progress")
    skill_node = relationship("SkillNode", back_populates="agent_progress")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('agent_id', 'skill_node_id', name='uq_agent_skill'),
    )
```

#### 4. `app/models/progression_path.py`
```python
"""
Progression path model for skill trees.
Defines recommended skill sequences and learning paths.
"""

from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class ProgressionPath(Base):
    __tablename__ = "progression_paths"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_tree_id = Column(String, ForeignKey("skill_trees.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Path configuration
    skill_sequence = Column(JSON, nullable=False)  # Ordered array of skill_node IDs
    estimated_duration_weeks = Column(Integer, nullable=True)
    
    # Specialization
    specialization = Column(String, nullable=False, index=True)
    
    # Customization
    is_custom = Column(Boolean, default=False)
    creator_id = Column(String, nullable=True)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, onupdate="CURRENT_TIMESTAMP")
    
    # Relationships
    skill_tree = relationship("SkillTree", back_populates="progression_paths")
```

---

### Services (4 files)

#### 5. `app/services/specialization_service.py`
- CRUD operations for specialization profiles
- Validation of specialization types
- Cross-specialization penalty calculations
- Tool/curriculum recommendations based on specialization

#### 6. `app/services/skill_tree_service.py`
- CRUD operations for skill trees and nodes
- Prerequisite validation
- Skill tree visualization data generation
- Custom skill tree creation

#### 7. `app/services/skill_progress_service.py`
- Track agent progress through skill nodes
- Experience gain and leveling
- Unlock skill nodes when prerequisites met
- Apply bonuses from completed skills

#### 8. `app/services/progression_path_service.py`
- CRUD operations for progression paths
- Path validation (check skill sequence is valid)
- Recommend paths based on specialization
- Track agent progress through paths

---

### API Endpoints (4 files)

#### 9. `app/api/v1/endpoints/specializations.py`
```
POST   /api/v1/agents/{agent_id}/specialization     - Create specialization profile
GET    /api/v1/agents/{agent_id}/specialization     - Get specialization profile
PATCH  /api/v1/agents/{agent_id}/specialization     - Update specialization profile
DELETE /api/v1/agents/{agent_id}/specialization     - Delete specialization profile

GET    /api/v1/specializations/types                - List available specialization types
GET    /api/v1/specializations/{type}/tools         - Get recommended tools for specialization
GET    /api/v1/specializations/{type}/curriculum    - Get recommended curriculum
```

#### 10. `app/api/v1/endpoints/skill_trees.py`
```
POST   /api/v1/skill-trees                          - Create skill tree
GET    /api/v1/skill-trees                          - List skill trees
GET    /api/v1/skill-trees/{tree_id}                - Get skill tree
PATCH  /api/v1/skill-trees/{tree_id}                - Update skill tree
DELETE /api/v1/skill-trees/{tree_id}                - Delete skill tree

POST   /api/v1/skill-trees/{tree_id}/nodes          - Add skill node
GET    /api/v1/skill-trees/{tree_id}/nodes          - List skill nodes
PATCH  /api/v1/skill-trees/{tree_id}/nodes/{node_id} - Update skill node
DELETE /api/v1/skill-trees/{tree_id}/nodes/{node_id} - Delete skill node

GET    /api/v1/skill-trees/specialization/{type}    - Get trees for specialization
```

#### 11. `app/api/v1/endpoints/skill_progress.py`
```
GET    /api/v1/agents/{agent_id}/skills             - Get all skill progress
GET    /api/v1/agents/{agent_id}/skills/{node_id}   - Get specific skill progress
POST   /api/v1/agents/{agent_id}/skills/{node_id}/gain-xp - Add experience
POST   /api/v1/agents/{agent_id}/skills/{node_id}/unlock  - Unlock skill (if prerequisites met)

GET    /api/v1/agents/{agent_id}/skills/unlocked    - Get unlocked skills
GET    /api/v1/agents/{agent_id}/skills/available   - Get available skills (prerequisites met)
```

#### 12. `app/api/v1/endpoints/progression_paths.py`
```
POST   /api/v1/progression-paths                    - Create progression path
GET    /api/v1/progression-paths                    - List progression paths
GET    /api/v1/progression-paths/{path_id}          - Get progression path
PATCH  /api/v1/progression-paths/{path_id}          - Update progression path
DELETE /api/v1/progression-paths/{path_id}          - Delete progression path

GET    /api/v1/progression-paths/specialization/{type} - Get paths for specialization
GET    /api/v1/agents/{agent_id}/progression-path   - Get agent's current path
POST   /api/v1/agents/{agent_id}/progression-path   - Assign path to agent
```

---

### Migrations (5 files)

#### 13. `alembic/versions/002_add_specialization_profiles.py`
- Create specialization_profiles table
- Add indexes

#### 14. `alembic/versions/003_add_skill_trees.py`
- Create skill_trees table
- Create skill_nodes table
- Add indexes and foreign keys

#### 15. `alembic/versions/004_add_agent_skill_progress.py`
- Create agent_skill_progress table
- Add unique constraint on (agent_id, skill_node_id)
- Add indexes

#### 16. `alembic/versions/005_add_progression_paths.py`
- Create progression_paths table
- Add indexes

#### 17. Update `app/models/agent.py`
- Add relationship to specialization_profile
- Add relationship to skill_progress

---

## 📝 Files to Modify (1 file)

### 1. `app/models/agent.py`
Add relationships:
```python
# In Agent model class
specialization_profile = relationship("SpecializationProfile", back_populates="agent", uselist=False)
skill_progress = relationship("AgentSkillProgress", back_populates="agent")
```

---

## 🧪 Test Files to Create (4 files)

1. `tests/test_specialization_service.py`
2. `tests/test_skill_tree_service.py`
3. `tests/test_skill_progress_service.py`
4. `tests/test_progression_path_service.py`

---

## 📊 Summary

**Total Files**:
- **New**: 17 files (4 models + 4 services + 4 endpoints + 5 migrations)
- **Modified**: 1 file (agent.py)
- **Tests**: 4 files

**Total Lines of Code**: ~2,500 lines

---

**Status**: Ready for implementation  
**Next**: Begin creating database models

