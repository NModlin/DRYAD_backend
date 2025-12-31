"""
Budget Manager
The Lyceum - Level 5

Manages compute budget allocation and enforcement for research projects.
Prevents runaway experiments and ensures fair resource distribution.
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.logging.logger import StructuredLogger

logger = StructuredLogger("dryad.lyceum.budget_manager")


class ResearchBudget(BaseModel):
    """Research budget allocation."""
    budget_id: str
    professor_agent_id: str
    allocated_compute_hours: float
    consumed_compute_hours: float
    period_start: str
    period_end: str
    status: str  # active, exhausted, expired


class BudgetManager:
    """
    Level 5 Component: Budget Manager
    
    Manages compute budget allocation and enforcement.
    Tracks consumption and prevents runaway experiments.
    """
    
    def __init__(self, db: Session):
        self.db = db
        logger.log_info("budget_manager_initialized", {})
    
    def allocate_budget(
        self,
        professor_agent_id: str,
        compute_hours: float,
        period_days: int = 30
    ) -> ResearchBudget:
        """
        Allocate compute budget to a professor agent.
        
        Args:
            professor_agent_id: Professor agent identifier
            compute_hours: Allocated compute hours
            period_days: Budget period in days
            
        Returns:
            Created budget allocation
        """
        try:
            budget_id = f"budget_{uuid.uuid4().hex[:12]}"
            
            period_start = datetime.now()
            period_end = period_start + timedelta(days=period_days)
            
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO research_budgets (
                    budget_id, professor_agent_id, allocated_compute_hours,
                    consumed_compute_hours, period_start, period_end, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                budget_id,
                professor_agent_id,
                compute_hours,
                0.0,
                period_start.isoformat(),
                period_end.isoformat(),
                "active"
            ))
            
            connection.commit()
            
            logger.log_info(
                "budget_allocated",
                {
                    "budget_id": budget_id,
                    "professor_agent_id": professor_agent_id,
                    "compute_hours": compute_hours,
                    "period_days": period_days
                }
            )
            
            return ResearchBudget(
                budget_id=budget_id,
                professor_agent_id=professor_agent_id,
                allocated_compute_hours=compute_hours,
                consumed_compute_hours=0.0,
                period_start=period_start.isoformat(),
                period_end=period_end.isoformat(),
                status="active"
            )
            
        except Exception as e:
            logger.log_error("budget_allocation_failed", {"error": str(e)})
            raise
    
    def consume_budget(
        self,
        professor_agent_id: str,
        compute_hours: float
    ) -> bool:
        """
        Consume compute budget for an experiment.
        
        Args:
            professor_agent_id: Professor agent identifier
            compute_hours: Compute hours to consume
            
        Returns:
            True if consumption successful, False if insufficient budget
        """
        try:
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            # Get active budget
            cursor.execute("""
                SELECT budget_id, allocated_compute_hours, consumed_compute_hours
                FROM research_budgets
                WHERE professor_agent_id = ? AND status = 'active'
                ORDER BY period_start DESC
                LIMIT 1
            """, (professor_agent_id,))
            
            row = cursor.fetchone()
            
            if not row:
                logger.log_error(
                    "no_active_budget",
                    {"professor_agent_id": professor_agent_id}
                )
                return False
            
            budget_id, allocated, consumed = row
            remaining = allocated - consumed
            
            # Check if sufficient budget
            if remaining < compute_hours:
                logger.log_error(
                    "insufficient_budget",
                    {
                        "professor_agent_id": professor_agent_id,
                        "requested": compute_hours,
                        "remaining": remaining
                    }
                )
                
                # Mark budget as exhausted
                cursor.execute("""
                    UPDATE research_budgets
                    SET status = 'exhausted'
                    WHERE budget_id = ?
                """, (budget_id,))
                connection.commit()
                
                return False
            
            # Consume budget
            new_consumed = consumed + compute_hours
            cursor.execute("""
                UPDATE research_budgets
                SET consumed_compute_hours = ?
                WHERE budget_id = ?
            """, (new_consumed, budget_id))
            
            connection.commit()
            
            logger.log_info(
                "budget_consumed",
                {
                    "budget_id": budget_id,
                    "consumed": compute_hours,
                    "total_consumed": new_consumed,
                    "remaining": allocated - new_consumed
                }
            )
            
            return True
            
        except Exception as e:
            logger.log_error("budget_consumption_failed", {"error": str(e)})
            return False
    
    def get_budget(
        self,
        professor_agent_id: str
    ) -> Optional[ResearchBudget]:
        """
        Get active budget for a professor agent.
        
        Args:
            professor_agent_id: Professor agent identifier
            
        Returns:
            Active budget if found
        """
        try:
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT budget_id, professor_agent_id, allocated_compute_hours,
                       consumed_compute_hours, period_start, period_end, status
                FROM research_budgets
                WHERE professor_agent_id = ? AND status = 'active'
                ORDER BY period_start DESC
                LIMIT 1
            """, (professor_agent_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return ResearchBudget(
                budget_id=row[0],
                professor_agent_id=row[1],
                allocated_compute_hours=row[2],
                consumed_compute_hours=row[3],
                period_start=row[4],
                period_end=row[5],
                status=row[6]
            )
            
        except Exception as e:
            logger.log_error("budget_retrieval_failed", {"error": str(e)})
            return None
    
    def get_remaining_budget(
        self,
        professor_agent_id: str
    ) -> float:
        """
        Get remaining compute hours for a professor agent.
        
        Args:
            professor_agent_id: Professor agent identifier
            
        Returns:
            Remaining compute hours (0 if no active budget)
        """
        budget = self.get_budget(professor_agent_id)
        if not budget:
            return 0.0
        
        return budget.allocated_compute_hours - budget.consumed_compute_hours
    
    def expire_budgets(self):
        """Expire budgets that have passed their end date."""
        try:
            connection = self.db.connection().connection
            cursor = connection.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE research_budgets
                SET status = 'expired'
                WHERE status = 'active' AND period_end < ?
            """, (now,))
            
            expired_count = cursor.rowcount
            connection.commit()
            
            if expired_count > 0:
                logger.log_info(
                    "budgets_expired",
                    {"count": expired_count}
                )
            
        except Exception as e:
            logger.log_error("budget_expiration_failed", {"error": str(e)})

