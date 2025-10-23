"""
Guardrail Service

Service for runtime safety monitoring and enforcement of agent behavior.
Handles relevance checks, content filtering, token limits, and execution time monitoring.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.execution_guardrails import (
    ExecutionGuardrail, GuardrailConfiguration, GuardrailMetrics,
    GuardrailType, GuardrailSeverity, GuardrailAction,
    GuardrailConfigCreate, GuardrailViolationResponse
)

logger = logging.getLogger(__name__)


class GuardrailService:
    """Service for runtime guardrail enforcement."""
    
    def __init__(self, db: Session):
        self.db = db
        self._load_configurations()
    
    def _load_configurations(self):
        """Load active guardrail configurations."""
        self.configs = {}
        configs = self.db.query(GuardrailConfiguration).filter(
            GuardrailConfiguration.enabled == True
        ).all()
        
        for config in configs:
            self.configs[config.guardrail_type] = config
        
        logger.info(f"✅ Loaded {len(self.configs)} guardrail configurations")
    
    async def check_all_guardrails(
        self,
        execution_id: str,
        agent_id: str,
        input_text: str,
        output_text: str,
        execution_time_ms: int,
        token_count: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check all enabled guardrails against agent execution.
        
        Args:
            execution_id: ID of the agent execution
            agent_id: ID of the agent
            input_text: Input prompt/query
            output_text: Agent's output
            execution_time_ms: Execution time in milliseconds
            token_count: Number of tokens generated
            context: Additional context
            
        Returns:
            Dict with guardrail results and any violations
        """
        violations = []
        modified_output = output_text
        should_block = False
        
        try:
            # Check relevance
            if GuardrailType.RELEVANCE_CHECK in self.configs:
                result = await self._check_relevance(
                    execution_id, agent_id, input_text, output_text
                )
                if result["violated"]:
                    violations.append(result)
                    if result["action"] == GuardrailAction.BLOCK:
                        should_block = True
            
            # Check content safety
            if GuardrailType.CONTENT_FILTER in self.configs:
                result = await self._check_content_safety(
                    execution_id, agent_id, output_text
                )
                if result["violated"]:
                    violations.append(result)
                    if result["action"] == GuardrailAction.BLOCK:
                        should_block = True
                    elif result["action"] == GuardrailAction.MODIFY:
                        modified_output = result.get("modified_output", output_text)
            
            # Check token usage
            if GuardrailType.TOKEN_LIMIT in self.configs:
                result = await self._check_token_usage(
                    execution_id, agent_id, token_count
                )
                if result["violated"]:
                    violations.append(result)
                    if result["action"] == GuardrailAction.BLOCK:
                        should_block = True
            
            # Check execution time
            if GuardrailType.EXECUTION_TIME in self.configs:
                result = await self._check_execution_time(
                    execution_id, agent_id, execution_time_ms
                )
                if result["violated"]:
                    violations.append(result)
                    if result["action"] == GuardrailAction.BLOCK:
                        should_block = True
            
            # Update metrics
            await self._update_metrics(violations)
            
            return {
                "passed": len(violations) == 0,
                "should_block": should_block,
                "violations": violations,
                "modified_output": modified_output if modified_output != output_text else None,
                "total_checks": len(self.configs),
                "violations_count": len(violations)
            }
        
        except Exception as e:
            logger.error(f"❌ Guardrail check failed: {e}")
            raise
    
    async def _check_relevance(
        self,
        execution_id: str,
        agent_id: str,
        input_text: str,
        output_text: str
    ) -> Dict[str, Any]:
        """
        Check if output is relevant to input.
        
        Simple keyword-based relevance check. In production, this would use
        semantic similarity or a classifier model.
        """
        config = self.configs[GuardrailType.RELEVANCE_CHECK]
        
        # Simple heuristic: check if output contains key terms from input
        input_words = set(re.findall(r'\w+', input_text.lower()))
        output_words = set(re.findall(r'\w+', output_text.lower()))
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        input_words -= stop_words
        output_words -= stop_words
        
        # Calculate overlap
        overlap = len(input_words & output_words)
        relevance_score = overlap / len(input_words) if input_words else 0
        
        threshold = config.configuration.get("relevance_threshold", 0.2)
        violated = relevance_score < threshold
        
        if violated:
            await self._log_violation(
                execution_id=execution_id,
                agent_id=agent_id,
                guardrail_type=GuardrailType.RELEVANCE_CHECK,
                severity=config.severity,
                violation_details={
                    "relevance_score": relevance_score,
                    "threshold": threshold,
                    "input_length": len(input_text),
                    "output_length": len(output_text)
                },
                action_taken=config.action
            )
        
        return {
            "guardrail": "relevance_check",
            "violated": violated,
            "severity": config.severity.value,
            "action": config.action,
            "details": {
                "relevance_score": relevance_score,
                "threshold": threshold
            }
        }
    
    async def _check_content_safety(
        self,
        execution_id: str,
        agent_id: str,
        output_text: str
    ) -> Dict[str, Any]:
        """
        Check output for inappropriate content.
        
        Simple pattern-based filtering. In production, this would use
        content moderation APIs or ML models.
        """
        config = self.configs[GuardrailType.CONTENT_FILTER]
        
        # Check for PII patterns
        pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        
        detected_pii = []
        modified_output = output_text
        
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, output_text)
            if matches:
                detected_pii.append({
                    "type": pii_type,
                    "count": len(matches)
                })
                # Redact PII
                modified_output = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", modified_output)
        
        violated = len(detected_pii) > 0
        
        if violated:
            await self._log_violation(
                execution_id=execution_id,
                agent_id=agent_id,
                guardrail_type=GuardrailType.CONTENT_FILTER,
                severity=config.severity,
                violation_details={
                    "detected_pii": detected_pii,
                    "original_length": len(output_text),
                    "modified_length": len(modified_output)
                },
                action_taken=config.action
            )
        
        return {
            "guardrail": "content_filter",
            "violated": violated,
            "severity": config.severity.value,
            "action": config.action,
            "details": {
                "detected_pii": detected_pii
            },
            "modified_output": modified_output if violated else None
        }
    
    async def _check_token_usage(
        self,
        execution_id: str,
        agent_id: str,
        token_count: int
    ) -> Dict[str, Any]:
        """Check if token usage exceeds limits."""
        config = self.configs[GuardrailType.TOKEN_LIMIT]
        
        max_tokens = config.configuration.get("max_tokens", 4000)
        violated = token_count > max_tokens
        
        if violated:
            await self._log_violation(
                execution_id=execution_id,
                agent_id=agent_id,
                guardrail_type=GuardrailType.TOKEN_LIMIT,
                severity=config.severity,
                violation_details={
                    "token_count": token_count,
                    "max_tokens": max_tokens,
                    "excess_tokens": token_count - max_tokens
                },
                action_taken=config.action
            )
        
        return {
            "guardrail": "token_limit",
            "violated": violated,
            "severity": config.severity.value,
            "action": config.action,
            "details": {
                "token_count": token_count,
                "max_tokens": max_tokens
            }
        }
    
    async def _check_execution_time(
        self,
        execution_id: str,
        agent_id: str,
        execution_time_ms: int
    ) -> Dict[str, Any]:
        """Check if execution time exceeds limits."""
        config = self.configs[GuardrailType.EXECUTION_TIME]
        
        max_time_ms = config.configuration.get("max_execution_time_ms", 30000)
        violated = execution_time_ms > max_time_ms
        
        if violated:
            await self._log_violation(
                execution_id=execution_id,
                agent_id=agent_id,
                guardrail_type=GuardrailType.EXECUTION_TIME,
                severity=config.severity,
                violation_details={
                    "execution_time_ms": execution_time_ms,
                    "max_time_ms": max_time_ms,
                    "excess_time_ms": execution_time_ms - max_time_ms
                },
                action_taken=config.action
            )
        
        return {
            "guardrail": "execution_time",
            "violated": violated,
            "severity": config.severity.value,
            "action": config.action,
            "details": {
                "execution_time_ms": execution_time_ms,
                "max_time_ms": max_time_ms
            }
        }

    async def _log_violation(
        self,
        execution_id: str,
        agent_id: str,
        guardrail_type: GuardrailType,
        severity: GuardrailSeverity,
        violation_details: Dict[str, Any],
        action_taken: GuardrailAction
    ) -> None:
        """Log a guardrail violation."""
        try:
            config = self.configs.get(guardrail_type)

            violation = ExecutionGuardrail(
                execution_id=execution_id,
                agent_id=agent_id,
                guardrail_type=guardrail_type,
                config_id=config.id if config else None,
                severity=severity,
                violation_details=violation_details,
                action_taken=action_taken
            )

            self.db.add(violation)
            self.db.commit()

            logger.warning(
                f"⚠️ Guardrail violation: {guardrail_type.value} "
                f"(Severity: {severity.value}, Action: {action_taken.value})"
            )

        except Exception as e:
            logger.error(f"❌ Failed to log violation: {e}")
            # Don't raise - logging failure shouldn't break execution

    async def _update_metrics(self, violations: List[Dict[str, Any]]) -> None:
        """Update guardrail metrics."""
        try:
            for violation in violations:
                guardrail_type = GuardrailType(violation["guardrail"])
                config = self.configs.get(guardrail_type)

                if not config:
                    continue

                # Get or create metrics for today
                today = datetime.utcnow().date()
                metrics = self.db.query(GuardrailMetrics).filter(
                    and_(
                        GuardrailMetrics.config_id == config.id,
                        GuardrailMetrics.date == today
                    )
                ).first()

                if not metrics:
                    metrics = GuardrailMetrics(
                        config_id=config.id,
                        date=today,
                        total_checks=0,
                        violations_count=0,
                        blocks_count=0,
                        warnings_count=0,
                        modifications_count=0
                    )
                    self.db.add(metrics)

                metrics.total_checks += 1
                metrics.violations_count += 1

                action = GuardrailAction(violation["action"])
                if action == GuardrailAction.BLOCK:
                    metrics.blocks_count += 1
                elif action == GuardrailAction.WARN:
                    metrics.warnings_count += 1
                elif action == GuardrailAction.MODIFY:
                    metrics.modifications_count += 1

            self.db.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update metrics: {e}")
            # Don't raise - metrics update failure shouldn't break execution

    async def get_violation_history(
        self,
        agent_id: Optional[str] = None,
        guardrail_type: Optional[GuardrailType] = None,
        severity: Optional[GuardrailSeverity] = None,
        limit: int = 100
    ) -> List[ExecutionGuardrail]:
        """
        Get guardrail violation history with optional filters.

        Args:
            agent_id: Filter by agent ID
            guardrail_type: Filter by guardrail type
            severity: Filter by severity level
            limit: Maximum number of results

        Returns:
            List of guardrail violations
        """
        try:
            query = self.db.query(ExecutionGuardrail)

            if agent_id:
                query = query.filter(ExecutionGuardrail.agent_id == agent_id)

            if guardrail_type:
                query = query.filter(ExecutionGuardrail.guardrail_type == guardrail_type)

            if severity:
                query = query.filter(ExecutionGuardrail.severity == severity)

            violations = query.order_by(
                ExecutionGuardrail.timestamp.desc()
            ).limit(limit).all()

            return violations

        except Exception as e:
            logger.error(f"❌ Failed to get violation history: {e}")
            raise

    async def get_metrics_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get summary of guardrail metrics.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dict with metrics summary
        """
        try:
            query = self.db.query(GuardrailMetrics)

            if start_date:
                query = query.filter(GuardrailMetrics.date >= start_date.date())

            if end_date:
                query = query.filter(GuardrailMetrics.date <= end_date.date())

            metrics = query.all()

            total_checks = sum(m.total_checks for m in metrics)
            total_violations = sum(m.violations_count for m in metrics)
            total_blocks = sum(m.blocks_count for m in metrics)
            total_warnings = sum(m.warnings_count for m in metrics)
            total_modifications = sum(m.modifications_count for m in metrics)

            return {
                "total_checks": total_checks,
                "total_violations": total_violations,
                "total_blocks": total_blocks,
                "total_warnings": total_warnings,
                "total_modifications": total_modifications,
                "violation_rate": total_violations / total_checks if total_checks > 0 else 0,
                "period_days": len(set(m.date for m in metrics))
            }

        except Exception as e:
            logger.error(f"❌ Failed to get metrics summary: {e}")
            raise

