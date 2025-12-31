"""
Task Force Manager - Manages collaborative agent teams

Creates and manages Task Forces for complex tasks requiring
multi-agent collaboration with peer-to-peer communication.

Part of Level 3 Orchestration Service.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import json

from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("task_force_manager")


class TaskForceMember(BaseModel):
    """Task force member information."""
    member_id: str
    agent_id: str
    agent_role: str
    joined_at: str


class TaskForceMessage(BaseModel):
    """Task force communication message."""
    log_id: int
    agent_id: str
    message_type: str  # 'proposal', 'critique', 'refinement', 'agreement', 'question', 'answer'
    message_content: Dict[str, Any]
    timestamp: str


class TaskForce(BaseModel):
    """Task force information."""
    task_force_id: str
    objective: str
    status: str  # 'active', 'resolved', 'failed', 'paused'
    master_orchestrator_id: str
    created_at: str
    resolved_at: Optional[str] = None
    resolution_result: Optional[Dict[str, Any]] = None
    members: List[TaskForceMember] = []


class TaskForceManager:
    """
    Level 3 Component: Task Force Manager
    
    Manages lifecycle of collaborative agent teams (Task Forces)
    for complex tasks requiring multi-agent coordination.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize task force manager.
        
        Args:
            db_session: Database session for persistence
        """
        self.db = db_session
        logger.log_info("task_force_manager_initialized", {})
    
    async def create_task_force(
        self,
        objective: str,
        orchestrator_id: str,
        agent_roles: List[str]
    ) -> TaskForce:
        """
        Create a new task force.
        
        Args:
            objective: Task force objective
            orchestrator_id: ID of orchestrating agent
            agent_roles: Required agent specializations
            
        Returns:
            Created TaskForce
        """
        task_force_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        # Create task force record
        if self.db:
            try:
                query = """
                    INSERT INTO task_forces 
                    (task_force_id, objective, status, master_orchestrator_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                self.db.execute(
                    query,
                    (task_force_id, objective, "active", orchestrator_id, created_at)
                )
                self.db.commit()
            except Exception as e:
                logger.log_error("task_force_creation_failed", {"error": str(e)})
                raise
        
        # Assign agents to roles (mock implementation - would integrate with Agent Registry)
        members = []
        for role in agent_roles:
            member = await self._assign_agent_to_role(task_force_id, role)
            members.append(member)
        
        task_force = TaskForce(
            task_force_id=task_force_id,
            objective=objective,
            status="active",
            master_orchestrator_id=orchestrator_id,
            created_at=created_at,
            members=members
        )
        
        logger.log_info(
            "task_force_created",
            {
                "task_force_id": task_force_id,
                "num_members": len(members),
                "roles": agent_roles
            }
        )
        
        return task_force
    
    async def _assign_agent_to_role(
        self,
        task_force_id: str,
        role: str
    ) -> TaskForceMember:
        """Assign an agent to a role in the task force."""
        
        # Mock implementation: Generate agent ID based on role
        # In production, would query Agent Registry for best match
        agent_id = f"agent_{role.lower().replace(' ', '_')}"
        member_id = str(uuid.uuid4())
        joined_at = datetime.utcnow().isoformat()
        
        # Store in database
        if self.db:
            try:
                query = """
                    INSERT INTO task_force_members
                    (member_id, task_force_id, agent_id, agent_role, joined_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                self.db.execute(
                    query,
                    (member_id, task_force_id, agent_id, role, joined_at)
                )
                self.db.commit()
            except Exception as e:
                logger.log_error("member_assignment_failed", {"error": str(e)})
        
        return TaskForceMember(
            member_id=member_id,
            agent_id=agent_id,
            agent_role=role,
            joined_at=joined_at
        )
    
    async def send_message(
        self,
        task_force_id: str,
        agent_id: str,
        message_type: str,
        content: Dict[str, Any]
    ) -> TaskForceMessage:
        """
        Send a message to the task force.
        
        Args:
            task_force_id: Task force ID
            agent_id: Sending agent ID
            message_type: Type of message
            content: Message content
            
        Returns:
            Created TaskForceMessage
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Store in database
        log_id = None
        if self.db:
            try:
                query = """
                    INSERT INTO task_force_logs
                    (task_force_id, agent_id, message_type, message_content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor = self.db.execute(
                    query,
                    (task_force_id, agent_id, message_type, json.dumps(content), timestamp)
                )
                log_id = cursor.lastrowid
                self.db.commit()
            except Exception as e:
                logger.log_error("message_send_failed", {"error": str(e)})
                raise
        
        message = TaskForceMessage(
            log_id=log_id or 0,
            agent_id=agent_id,
            message_type=message_type,
            message_content=content,
            timestamp=timestamp
        )
        
        logger.log_info(
            "task_force_message_sent",
            {
                "task_force_id": task_force_id,
                "agent_id": agent_id,
                "message_type": message_type
            }
        )
        
        return message
    
    async def get_messages(
        self,
        task_force_id: str,
        limit: int = 100
    ) -> List[TaskForceMessage]:
        """
        Get task force conversation history.
        
        Args:
            task_force_id: Task force ID
            limit: Maximum messages to retrieve
            
        Returns:
            List of TaskForceMessage
        """
        if not self.db:
            return []
        
        try:
            query = """
                SELECT log_id, agent_id, message_type, message_content, timestamp
                FROM task_force_logs
                WHERE task_force_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """
            cursor = self.db.execute(query, (task_force_id, limit))
            rows = cursor.fetchall()
            
            messages = []
            for row in rows:
                messages.append(
                    TaskForceMessage(
                        log_id=row[0],
                        agent_id=row[1],
                        message_type=row[2],
                        message_content=json.loads(row[3]),
                        timestamp=row[4]
                    )
                )
            
            return messages
        except Exception as e:
            logger.log_error("message_retrieval_failed", {"error": str(e)})
            return []
    
    async def resolve_task_force(
        self,
        task_force_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Resolve a task force with final result.
        
        Args:
            task_force_id: Task force ID
            result: Final collaborative result
            
        Returns:
            True if successful
        """
        resolved_at = datetime.utcnow().isoformat()
        
        if self.db:
            try:
                query = """
                    UPDATE task_forces
                    SET status = ?, resolved_at = ?, resolution_result = ?
                    WHERE task_force_id = ?
                """
                self.db.execute(
                    query,
                    ("resolved", resolved_at, json.dumps(result), task_force_id)
                )
                self.db.commit()
                
                logger.log_info(
                    "task_force_resolved",
                    {"task_force_id": task_force_id}
                )
                return True
            except Exception as e:
                logger.log_error("task_force_resolution_failed", {"error": str(e)})
                return False
        
        return False
    
    async def get_task_force(self, task_force_id: str) -> Optional[TaskForce]:
        """Get task force by ID."""
        if not self.db:
            return None
        
        try:
            # Get task force
            query = "SELECT * FROM task_forces WHERE task_force_id = ?"
            cursor = self.db.execute(query, (task_force_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get members
            members_query = "SELECT * FROM task_force_members WHERE task_force_id = ?"
            members_cursor = self.db.execute(members_query, (task_force_id,))
            member_rows = members_cursor.fetchall()
            
            members = [
                TaskForceMember(
                    member_id=m[0],
                    agent_id=m[2],
                    agent_role=m[3],
                    joined_at=m[4]
                )
                for m in member_rows
            ]
            
            return TaskForce(
                task_force_id=row[0],
                objective=row[1],
                status=row[2],
                master_orchestrator_id=row[3],
                created_at=row[4],
                resolved_at=row[5],
                resolution_result=json.loads(row[6]) if row[6] else None,
                members=members
            )
        except Exception as e:
            logger.log_error("task_force_retrieval_failed", {"error": str(e)})
            return None

