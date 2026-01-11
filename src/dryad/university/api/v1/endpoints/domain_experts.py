"""
Domain Expert API Endpoints

RESTful API endpoints for domain expert agents:
- Expert agent registration and management
- Tutoring session creation and management
- Learning path generation and tracking
- Knowledge base queries and updates
- Expert session analytics and reporting
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timezone

from dryad.university.database.database import get_db
from dryad.university.database.models_university import UniversityAgent, DomainExpertProfile, ExpertSession
from dryad.university.services.domain_expert_engine import DomainExpertEngine
from dryad.university.services.adaptive_learning import AdaptiveLearningSystem
from dryad.university.services.knowledge_management import KnowledgeManagementSystem, KnowledgeType, QualityLevel

# Import expert agents
from dryad.university.agents.domain_experts.math_expert import MathematicsExpertAgent
from dryad.university.agents.domain_experts.science_expert import ScienceExpertAgent
from dryad.university.agents.domain_experts.language_expert import LanguageExpertAgent
from dryad.university.agents.domain_experts.history_expert import HistoryExpertAgent
from dryad.university.agents.domain_experts.cs_expert import ComputerScienceExpertAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/domain-experts", tags=["domain-experts"])

# Global instances (in production, these would be managed by dependency injection)
expert_engine = None
adaptive_system = None
knowledge_system = None

def get_expert_engine(db: Session = Depends(get_db)):
    """Get DomainExpertEngine instance"""
    global expert_engine, adaptive_system, knowledge_system
    
    if expert_engine is None:
        expert_engine = DomainExpertEngine(db)
        adaptive_system = AdaptiveLearningSystem(db)
        knowledge_system = KnowledgeManagementSystem(db)
    
    return expert_engine

def get_adaptive_system(db: Session = Depends(get_db)):
    """Get AdaptiveLearningSystem instance"""
    global adaptive_system
    return adaptive_system

def get_knowledge_system(db: Session = Depends(get_db)):
    """Get KnowledgeManagementSystem instance"""
    global knowledge_system
    return knowledge_system

# ==================== Expert Agent Management Endpoints ====================

@router.get("/agents")
async def list_domain_experts(
    domain: Optional[str] = None,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """List all domain expert agents"""
    try:
        experts = expert_engine.list_expert_agents(domain, status)
        return {"experts": experts}
    except Exception as e:
        logger.error(f"Error listing experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}")
async def get_domain_expert(
    agent_id: str,
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Get details of a specific domain expert agent"""
    try:
        expert = expert_engine.get_expert_agent(agent_id)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert agent not found")
        return expert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting expert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents")
async def register_domain_expert(
    agent_data: Dict[str, Any],
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Register a new domain expert agent"""
    try:
        expert = expert_engine.register_expert_agent(agent_data)
        return {"message": "Expert agent registered successfully", "expert": expert}
    except Exception as e:
        logger.error(f"Error registering expert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/agents/{agent_id}")
async def update_domain_expert(
    agent_id: str,
    agent_data: Dict[str, Any],
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Update an existing domain expert agent"""
    try:
        expert = expert_engine.update_expert_agent(agent_id, agent_data)
        if not expert:
            raise HTTPException(status_code=404, detail="Expert agent not found")
        return {"message": "Expert agent updated successfully", "expert": expert}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating expert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def delete_domain_expert(
    agent_id: str,
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Delete a domain expert agent"""
    try:
        success = expert_engine.delete_expert_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Expert agent not found")
        return {"message": "Expert agent deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting expert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Tutoring Session Endpoints ====================

@router.post("/sessions/tutoring")
async def create_tutoring_session(
    session_request: Dict[str, Any],
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Create a new tutoring session with an expert agent"""
    try:
        domain = session_request.get("domain")
        student_id = session_request.get("student_id")
        topic = session_request.get("topic")
        difficulty_level = session_request.get("difficulty_level", "intermediate")
        learning_objectives = session_request.get("learning_objectives", [])
        
        if not all([domain, student_id, topic]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Select appropriate expert agent based on domain
        session_data = await _create_domain_specific_session(
            domain, student_id, topic, difficulty_level, learning_objectives, db
        )
        
        return {"message": "Tutoring session created successfully", "session": session_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tutoring session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_tutoring_session(
    session_id: str,
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Get details of a tutoring session"""
    try:
        session = expert_engine.get_expert_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_tutoring_sessions(
    expert_id: Optional[str] = None,
    student_id: Optional[str] = None,
    domain: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """List tutoring sessions with optional filters"""
    try:
        sessions = expert_engine.list_expert_sessions(
            expert_id=expert_id,
            student_id=student_id,
            domain=domain,
            status=status,
            limit=limit,
            offset=offset
        )
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status_update: Dict[str, Any],
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Update the status of a tutoring session"""
    try:
        new_status = status_update.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        session = expert_engine.update_session_status(session_id, new_status)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session status updated successfully", "session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Learning Path Endpoints ====================

@router.post("/learning-paths/generate")
async def generate_learning_path(
    path_request: Dict[str, Any],
    db: Session = Depends(get_db),
    knowledge_system: KnowledgeManagementSystem = Depends(get_knowledge_system)
):
    """Generate a personalized learning path"""
    try:
        student_profile = path_request.get("student_profile")
        target_domain = path_request.get("domain")
        learning_objectives = path_request.get("learning_objectives", [])
        preferred_learning_style = path_request.get("preferred_learning_style")
        
        if not all([student_profile, target_domain, learning_objectives]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        learning_path = await knowledge_system.create_learning_path(
            student_profile=student_profile,
            target_domain=target_domain,
            learning_objectives=learning_objectives,
            preferred_learning_style=preferred_learning_style
        )
        
        if "error" in learning_path:
            raise HTTPException(status_code=400, detail=learning_path["error"])
        
        return {"message": "Learning path generated successfully", "learning_path": learning_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating learning path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning-paths/{path_id}")
async def get_learning_path(
    path_id: str,
    db: Session = Depends(get_db),
    knowledge_system: KnowledgeManagementSystem = Depends(get_knowledge_system)
):
    """Get details of a learning path"""
    try:
        # This would typically fetch from a learning paths table
        # For now, return a placeholder response
        return {"learning_path_id": path_id, "status": "active", "progress": 0.0}
    except Exception as e:
        logger.error(f"Error getting learning path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Knowledge Base Endpoints ====================

@router.get("/knowledge/{domain}")
async def get_domain_knowledge(
    domain: str,
    knowledge_type: Optional[str] = None,
    quality_level: Optional[str] = None,
    topic_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    knowledge_system: KnowledgeManagementSystem = Depends(get_knowledge_system)
):
    """Retrieve knowledge base for a specific domain"""
    try:
        knowledge_type_enum = KnowledgeType(knowledge_type) if knowledge_type else None
        quality_level_enum = QualityLevel(quality_level) if quality_level else None
        
        knowledge_base = await knowledge_system.retrieve_knowledge_base(
            domain=domain,
            knowledge_type=knowledge_type_enum,
            quality_level=quality_level_enum,
            topic_filter=topic_filter,
            limit=limit
        )
        
        if "error" in knowledge_base:
            raise HTTPException(status_code=400, detail=knowledge_base["error"])
        
        return knowledge_base
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/store")
async def store_expert_knowledge(
    knowledge_request: Dict[str, Any],
    db: Session = Depends(get_db),
    knowledge_system: KnowledgeManagementSystem = Depends(get_knowledge_system)
):
    """Store expert knowledge in the knowledge base"""
    try:
        expert_agent_id = knowledge_request.get("expert_agent_id")
        domain = knowledge_request.get("domain")
        knowledge_type = knowledge_request.get("knowledge_type")
        content = knowledge_request.get("content")
        quality_level = knowledge_request.get("quality_level", "intermediate")
        validation_required = knowledge_request.get("validation_required", True)
        
        if not all([expert_agent_id, domain, knowledge_type, content]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        knowledge_type_enum = KnowledgeType(knowledge_type)
        quality_level_enum = QualityLevel(quality_level)
        
        knowledge_entry = await knowledge_system.store_expert_knowledge(
            expert_agent_id=expert_agent_id,
            domain=domain,
            knowledge_type=knowledge_type_enum,
            content=content,
            quality_level=quality_level_enum,
            validation_required=validation_required
        )
        
        if "error" in knowledge_entry:
            raise HTTPException(status_code=400, detail=knowledge_entry["error"])
        
        return {"message": "Expert knowledge stored successfully", "knowledge_entry": knowledge_entry}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing expert knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/validate")
async def validate_knowledge_entries(
    validation_request: Dict[str, Any],
    db: Session = Depends(get_db),
    knowledge_system: KnowledgeManagementSystem = Depends(get_knowledge_system)
):
    """Validate the quality of knowledge entries"""
    try:
        knowledge_entries = validation_request.get("knowledge_entries", [])
        validation_criteria = validation_request.get("validation_criteria")
        
        if not knowledge_entries:
            raise HTTPException(status_code=400, detail="No knowledge entries provided")
        
        validation_results = await knowledge_system.validate_knowledge_quality(
            knowledge_entries=knowledge_entries,
            validation_criteria=validation_criteria
        )
        
        if "error" in validation_results:
            raise HTTPException(status_code=400, detail=validation_results["error"])
        
        return {"message": "Knowledge validation completed", "validation_results": validation_results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Analytics and Reporting Endpoints ====================

@router.get("/analytics/expert-performance")
async def get_expert_performance_analytics(
    expert_id: Optional[str] = None,
    domain: Optional[str] = None,
    time_period: str = "30d",
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Get analytics on expert agent performance"""
    try:
        analytics = expert_engine.get_expert_analytics(
            expert_id=expert_id,
            domain=domain,
            time_period=time_period
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting expert analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/student-progress")
async def get_student_progress_analytics(
    student_id: Optional[str] = None,
    domain: Optional[str] = None,
    time_period: str = "30d",
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Get analytics on student progress through expert sessions"""
    try:
        analytics = expert_engine.get_student_progress_analytics(
            student_id=student_id,
            domain=domain,
            time_period=time_period
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting student progress analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/session-outcomes")
async def get_session_outcomes_analytics(
    domain: Optional[str] = None,
    time_period: str = "30d",
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Get analytics on session outcomes and effectiveness"""
    try:
        analytics = expert_engine.get_session_outcomes_analytics(
            domain=domain,
            time_period=time_period
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting session outcomes analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Helper Functions ====================

async def _create_domain_specific_session(
    domain: str,
    student_id: str,
    topic: str,
    difficulty_level: str,
    learning_objectives: List[str],
    db: Session
) -> Dict[str, Any]:
    """Create domain-specific tutoring session"""
    
    # Initialize services
    expert_engine = DomainExpertEngine(db)
    adaptive_system = AdaptiveLearningSystem(db)
    
    if domain == "mathematics":
        expert_agent = MathematicsExpertAgent(db, expert_engine, adaptive_system)
        return await expert_agent.provide_math_tutoring(
            student_id=student_id,
            topic=topic,
            difficulty_level=difficulty_level,
            learning_objectives=learning_objectives
        )
    
    elif domain == "science":
        expert_agent = ScienceExpertAgent(db, expert_engine, adaptive_system)
        return await expert_agent.provide_science_tutoring(
            student_id=student_id,
            topic=topic,
            difficulty_level=difficulty_level,
            learning_objectives=learning_objectives
        )
    
    elif domain == "language":
        expert_agent = LanguageExpertAgent(db, expert_engine, adaptive_system)
        return await expert_agent.provide_language_tutoring(
            student_id=student_id,
            topic=topic,
            difficulty_level=difficulty_level,
            learning_objectives=learning_objectives
        )
    
    elif domain == "history":
        expert_agent = HistoryExpertAgent(db, expert_engine, adaptive_system)
        return await expert_agent.provide_history_tutoring(
            student_id=student_id,
            topic=topic,
            difficulty_level=difficulty_level,
            learning_objectives=learning_objectives
        )
    
    elif domain == "computer_science":
        expert_agent = ComputerScienceExpertAgent(db, expert_engine, adaptive_system)
        return await expert_agent.provide_cs_tutoring(
            student_id=student_id,
            topic=topic,
            difficulty_level=difficulty_level,
            learning_objectives=learning_objectives
        )
    
    else:
        raise ValueError(f"Unsupported domain: {domain}")

# ==================== Background Tasks ====================

@router.post("/background/optimize-knowledge-base")
async def optimize_knowledge_base(
    background_tasks: BackgroundTasks,
    domain: Optional[str] = None,
    db: Session = Depends(get_db),
    knowledge_system: KnowledgeManagementSystem = Depends(get_knowledge_system)
):
    """Background task to optimize the knowledge base"""
    try:
        # This would trigger a background optimization process
        return {"message": "Knowledge base optimization started", "task_id": str(uuid.uuid4())}
    except Exception as e:
        logger.error(f"Error starting knowledge base optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/background/train-expert-agents")
async def train_expert_agents(
    background_tasks: BackgroundTasks,
    domains: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    expert_engine: DomainExpertEngine = Depends(get_expert_engine)
):
    """Background task to train/update expert agents"""
    try:
        # This would trigger background agent training
        return {"message": "Expert agent training started", "task_id": str(uuid.uuid4())}
    except Exception as e:
        logger.error(f"Error starting expert agent training: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))