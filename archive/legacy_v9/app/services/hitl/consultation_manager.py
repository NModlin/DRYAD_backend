"""
Consultation Manager - Manages human consultation requests

Handles lifecycle of consultation requests:
- Request creation
- Message exchange
- Resolution
- Timeout handling

Part of Level 3 HITL Service.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import json

from app.services.hitl.state_manager import AgentStateManager
from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("consultation_manager")


class ConsultationMessage(BaseModel):
    """Consultation message."""
    message_id: int
    sender_type: str  # 'agent', 'human'
    sender_id: str
    message_content: Dict[str, Any]
    timestamp: str


class ConsultationRequest(BaseModel):
    """Consultation request."""
    consultation_id: str
    agent_id: str
    task_id: str
    task_force_id: Optional[str] = None
    consultation_type: str  # 'approval', 'guidance', 'clarification', 'escalation'
    context: Dict[str, Any]
    status: str  # 'pending', 'in_progress', 'resolved', 'timeout'
    created_at: str
    resolved_at: Optional[str] = None
    resolution: Optional[Dict[str, Any]] = None
    timeout_at: str


class ConsultationManager:
    """
    Level 3 Component: Consultation Manager
    
    Manages human consultation requests during agent execution,
    enabling real-time human intervention and guidance.
    """
    
    # Default timeout for consultations (30 minutes)
    DEFAULT_TIMEOUT_MINUTES = 30
    
    def __init__(self, db_session=None):
        """
        Initialize consultation manager.
        
        Args:
            db_session: Database session for persistence
        """
        self.db = db_session
        self.state_manager = AgentStateManager()
        logger.log_info("consultation_manager_initialized", {})
    
    async def request_consultation(
        self,
        agent_id: str,
        task_id: str,
        consultation_type: str,
        context: Dict[str, Any],
        task_force_id: Optional[str] = None,
        timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES
    ) -> ConsultationRequest:
        """
        Request human consultation.
        
        Args:
            agent_id: Requesting agent ID
            task_id: Current task ID
            consultation_type: Type of consultation
            context: Task context
            task_force_id: Optional task force ID
            timeout_minutes: Timeout in minutes
            
        Returns:
            Created ConsultationRequest
        """
        consultation_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        timeout_at = created_at + timedelta(minutes=timeout_minutes)
        
        # Create consultation request
        request = ConsultationRequest(
            consultation_id=consultation_id,
            agent_id=agent_id,
            task_id=task_id,
            task_force_id=task_force_id,
            consultation_type=consultation_type,
            context=context,
            status="pending",
            created_at=created_at.isoformat(),
            timeout_at=timeout_at.isoformat()
        )
        
        # Store in database
        if self.db:
            try:
                query = """
                    INSERT INTO consultation_requests
                    (consultation_id, agent_id, task_id, task_force_id, 
                     consultation_type, context, status, created_at, timeout_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.db.execute(
                    query,
                    (
                        consultation_id,
                        agent_id,
                        task_id,
                        task_force_id,
                        consultation_type,
                        json.dumps(context),
                        "pending",
                        created_at.isoformat(),
                        timeout_at.isoformat()
                    )
                )
                self.db.commit()
            except Exception as e:
                logger.log_error("consultation_creation_failed", {"error": str(e)})
                raise
        
        # Pause agent
        await self.state_manager.pause_for_consultation(
            agent_id=agent_id,
            task_id=task_id,
            consultation_id=consultation_id
        )
        
        logger.log_info(
            "consultation_requested",
            {
                "consultation_id": consultation_id,
                "agent_id": agent_id,
                "consultation_type": consultation_type
            }
        )
        
        return request
    
    async def send_message(
        self,
        consultation_id: str,
        sender_type: str,
        sender_id: str,
        content: Dict[str, Any]
    ) -> ConsultationMessage:
        """
        Send a message in consultation.
        
        Args:
            consultation_id: Consultation ID
            sender_type: 'agent' or 'human'
            sender_id: Sender identifier
            content: Message content
            
        Returns:
            Created ConsultationMessage
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Store in database
        message_id = None
        if self.db:
            try:
                query = """
                    INSERT INTO consultation_messages
                    (consultation_id, sender_type, sender_id, message_content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor = self.db.execute(
                    query,
                    (consultation_id, sender_type, sender_id, json.dumps(content), timestamp)
                )
                message_id = cursor.lastrowid
                self.db.commit()
                
                # Update consultation status to in_progress if pending
                update_query = """
                    UPDATE consultation_requests
                    SET status = 'in_progress'
                    WHERE consultation_id = ? AND status = 'pending'
                """
                self.db.execute(update_query, (consultation_id,))
                self.db.commit()
            except Exception as e:
                logger.log_error("message_send_failed", {"error": str(e)})
                raise
        
        message = ConsultationMessage(
            message_id=message_id or 0,
            sender_type=sender_type,
            sender_id=sender_id,
            message_content=content,
            timestamp=timestamp
        )
        
        logger.log_info(
            "consultation_message_sent",
            {
                "consultation_id": consultation_id,
                "sender_type": sender_type
            }
        )
        
        return message
    
    async def get_messages(
        self,
        consultation_id: str
    ) -> List[ConsultationMessage]:
        """Get all messages for a consultation."""
        if not self.db:
            return []
        
        try:
            query = """
                SELECT message_id, sender_type, sender_id, message_content, timestamp
                FROM consultation_messages
                WHERE consultation_id = ?
                ORDER BY timestamp ASC
            """
            cursor = self.db.execute(query, (consultation_id,))
            rows = cursor.fetchall()
            
            messages = []
            for row in rows:
                messages.append(
                    ConsultationMessage(
                        message_id=row[0],
                        sender_type=row[1],
                        sender_id=row[2],
                        message_content=json.loads(row[3]),
                        timestamp=row[4]
                    )
                )
            
            return messages
        except Exception as e:
            logger.log_error("message_retrieval_failed", {"error": str(e)})
            return []
    
    async def resolve_consultation(
        self,
        consultation_id: str,
        resolution: Dict[str, Any]
    ) -> bool:
        """
        Resolve consultation with human decision.
        
        Args:
            consultation_id: Consultation ID
            resolution: Human decision/guidance
            
        Returns:
            True if successful
        """
        resolved_at = datetime.utcnow().isoformat()
        
        # Get consultation to find agent_id
        consultation = await self.get_consultation(consultation_id)
        if not consultation:
            logger.log_error("consultation_not_found", {"consultation_id": consultation_id})
            return False
        
        # Update consultation
        if self.db:
            try:
                query = """
                    UPDATE consultation_requests
                    SET status = ?, resolved_at = ?, resolution = ?
                    WHERE consultation_id = ?
                """
                self.db.execute(
                    query,
                    ("resolved", resolved_at, json.dumps(resolution), consultation_id)
                )
                self.db.commit()
            except Exception as e:
                logger.log_error("consultation_resolution_failed", {"error": str(e)})
                return False
        
        # Resume agent
        await self.state_manager.resume_from_consultation(
            agent_id=consultation.agent_id,
            resolution=resolution
        )
        
        logger.log_info(
            "consultation_resolved",
            {"consultation_id": consultation_id}
        )
        
        return True
    
    async def get_consultation(
        self,
        consultation_id: str
    ) -> Optional[ConsultationRequest]:
        """Get consultation by ID."""
        if not self.db:
            return None
        
        try:
            query = "SELECT * FROM consultation_requests WHERE consultation_id = ?"
            cursor = self.db.execute(query, (consultation_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return ConsultationRequest(
                consultation_id=row[0],
                agent_id=row[1],
                task_id=row[2],
                task_force_id=row[3],
                consultation_type=row[4],
                context=json.loads(row[5]),
                status=row[6],
                created_at=row[7],
                resolved_at=row[8],
                resolution=json.loads(row[9]) if row[9] else None,
                timeout_at=row[10]
            )
        except Exception as e:
            logger.log_error("consultation_retrieval_failed", {"error": str(e)})
            return None
    
    async def get_pending_consultations(self) -> List[ConsultationRequest]:
        """Get all pending consultations."""
        if not self.db:
            return []
        
        try:
            query = """
                SELECT * FROM consultation_requests
                WHERE status IN ('pending', 'in_progress')
                ORDER BY created_at ASC
            """
            cursor = self.db.execute(query)
            rows = cursor.fetchall()
            
            consultations = []
            for row in rows:
                consultations.append(
                    ConsultationRequest(
                        consultation_id=row[0],
                        agent_id=row[1],
                        task_id=row[2],
                        task_force_id=row[3],
                        consultation_type=row[4],
                        context=json.loads(row[5]),
                        status=row[6],
                        created_at=row[7],
                        resolved_at=row[8],
                        resolution=json.loads(row[9]) if row[9] else None,
                        timeout_at=row[10]
                    )
                )
            
            return consultations
        except Exception as e:
            logger.log_error("pending_consultations_retrieval_failed", {"error": str(e)})
            return []

