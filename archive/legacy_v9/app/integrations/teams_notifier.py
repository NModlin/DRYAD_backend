"""
Microsoft Teams Integration for Self-Healing Notifications
Sends Adaptive Cards for human review in the GAD framework.
"""

import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TeamsNotifier:
    """
    Microsoft Teams notification service.
    
    Sends Adaptive Cards to Teams channels for human review
    of self-healing fix plans.
    """
    
    def __init__(self, webhook_url: Optional[str] = None, callback_url: Optional[str] = None):
        """
        Initialize Teams notifier.
        
        Args:
            webhook_url: Teams incoming webhook URL
            callback_url: Public URL for callback actions
        """
        self.webhook_url = webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
        self.callback_url = callback_url or os.getenv("PUBLIC_CALLBACK_URL", "http://localhost:8000")
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            logger.warning("Teams notifications disabled: TEAMS_WEBHOOK_URL not configured")
    
    async def send_review_card(self, task: Dict[str, Any]) -> bool:
        """
        Send review request card to Teams.
        
        Args:
            task: Self-healing task dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Teams notifications disabled, skipping")
            return False
        
        try:
            card = self._build_review_card(task)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Teams notification sent for task {task['id']}")
                    return True
                else:
                    logger.error(f"Failed to send Teams notification: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending Teams notification: {e}", exc_info=True)
            return False
    
    def _build_review_card(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Build Adaptive Card for review request."""
        task_id = task["id"]
        error_type = task["error_type"]
        error_message = task["error_message"]
        file_path = task["file_path"]
        line_number = task["line_number"]
        severity = task["severity"]
        goal = task["goal"]
        plan = task.get("plan", {})
        
        # Format severity with emoji
        severity_emoji = {
            "critical": "[CRITICAL]",
            "high": "[HIGH]",
            "medium": "[MEDIUM]",
            "low": "[LOW]"
        }
        severity_display = f"{severity_emoji.get(severity, '[UNKNOWN]')} {severity.upper()}"
        
        # Build plan summary
        plan_summary = self._format_plan_summary(plan)
        
        # Build card
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "Self-Healing Fix Pending Review",
                                "weight": "bolder",
                                "size": "large",
                                "color": "attention"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Task ID: `{task_id}`",
                                "size": "small",
                                "isSubtle": True,
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "Error Type",
                                        "value": error_type
                                    },
                                    {
                                        "title": "Severity",
                                        "value": severity_display
                                    },
                                    {
                                        "title": "Location",
                                        "value": f"{file_path}:{line_number}"
                                    },
                                    {
                                        "title": "Detected",
                                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                ]
                            },
                            {
                                "type": "TextBlock",
                                "text": "**Error Message:**",
                                "weight": "bolder",
                                "spacing": "medium"
                            },
                            {
                                "type": "TextBlock",
                                "text": error_message,
                                "wrap": True,
                                "color": "attention"
                            },
                            {
                                "type": "TextBlock",
                                "text": "**Proposed Fix:**",
                                "weight": "bolder",
                                "spacing": "medium"
                            },
                            {
                                "type": "TextBlock",
                                "text": goal,
                                "wrap": True
                            }
                        ],
                        "actions": [
                            {
                                "type": "Action.Http",
                                "title": "Approve Fix",
                                "method": "POST",
                                "url": f"{self.callback_url}/api/v1/orchestrator/self-healing/review/{task_id}",
                                "body": '{"decision": "approved", "reviewer": "{{{{user.email}}}}"}'
                            },
                            {
                                "type": "Action.Http",
                                "title": "Reject Fix",
                                "method": "POST",
                                "url": f"{self.callback_url}/api/v1/orchestrator/self-healing/review/{task_id}",
                                "body": '{"decision": "rejected", "reviewer": "{{{{user.email}}}}"}'
                            },
                            {
                                "type": "Action.OpenUrl",
                                "title": "View & Review",
                                "url": f"{self.callback_url}/api/v1/self-healing-ui/tasks/{task_id}"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Add plan details if available
        if plan_summary:
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": "**Plan Details:**",
                "weight": "bolder",
                "spacing": "medium"
            })
            card["attachments"][0]["content"]["body"].append({
                "type": "TextBlock",
                "text": plan_summary,
                "wrap": True,
                "size": "small"
            })
        
        return card
    
    def _format_plan_summary(self, plan: Dict[str, Any]) -> str:
        """Format plan details for display."""
        if not plan:
            return ""
        
        changes = plan.get("changes", [])
        if not changes:
            return "No detailed plan available"
        
        summary_parts = []
        
        for i, change in enumerate(changes, 1):
            file = change.get("file", "unknown")
            rationale = change.get("rationale", "No rationale provided")
            summary_parts.append(f"{i}. {file}: {rationale}")
        
        tests = plan.get("tests_to_run", [])
        if tests:
            summary_parts.append(f"\n**Tests:** {', '.join(tests)}")
        
        return "\n".join(summary_parts)
    
    async def send_completion_notification(self, task: Dict[str, Any], success: bool) -> bool:
        """
        Send notification when task is completed.
        
        Args:
            task: Self-healing task dictionary
            success: Whether the fix was successful
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            card = self._build_completion_card(task, success)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                )
                
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}")
            return False
    
    def _build_completion_card(self, task: Dict[str, Any], success: bool) -> Dict[str, Any]:
        """Build Adaptive Card for completion notification."""
        task_id = task["id"]
        error_type = task["error_type"]
        file_path = task["file_path"]
        
        if success:
            title = "Self-Healing Fix Applied Successfully"
            color = "good"
            message = f"The fix for {error_type} in {file_path} has been applied and validated."
        else:
            title = "Self-Healing Fix Failed"
            color = "attention"
            message = f"The fix for {error_type} in {file_path} failed validation and was rolled back."
        
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": title,
                                "weight": "bolder",
                                "size": "large",
                                "color": color
                            },
                            {
                                "type": "TextBlock",
                                "text": message,
                                "wrap": True
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Task ID: `{task_id}`",
                                "size": "small",
                                "isSubtle": True,
                                "wrap": True
                            }
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "View Details",
                                "url": f"{self.callback_url}/api/v1/self-healing-ui/tasks/{task_id}"
                            }
                        ]
                    }
                }
            ]
        }


# Global instance
teams_notifier = TeamsNotifier()


async def send_review_notification(task: Dict[str, Any]) -> bool:
    """Send review notification to Teams."""
    return await teams_notifier.send_review_card(task)


async def send_completion_notification(task: Dict[str, Any], success: bool) -> bool:
    """Send completion notification to Teams."""
    return await teams_notifier.send_completion_notification(task, success)

