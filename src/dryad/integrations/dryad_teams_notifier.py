"""
DRYAD Teams Channel Integration
Sends bidirectional communication updates to Microsoft Teams channel.
"""

import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DRYADTeamsNotifier:
    """
    Microsoft Teams notification service for DRYAD integration updates.
    
    Sends Adaptive Cards to Teams channels for:
    - Deployment package received
    - Client startup events
    - Webhook instruction sent
    - Webhook instruction executed
    - Integration milestones
    - Errors and warnings
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize DRYAD Teams notifier.
        
        Args:
            webhook_url: Teams incoming webhook URL for DRYAD channel
        """
        self.webhook_url = webhook_url or os.getenv("DRYAD_TEAMS_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            logger.warning("DRYAD Teams notifications disabled: DRYAD_TEAMS_WEBHOOK_URL not configured")
    
    async def send_deployment_received(self, client_id: str, deployment_data: Dict[str, Any]) -> bool:
        """
        Notify when deployment package is received from client.
        
        Args:
            client_id: Client identifier
            deployment_data: Deployment package data
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            card = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "📦 Deployment Package Received",
                                "weight": "bolder",
                                "size": "large",
                                "color": "good"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Client **{client_id}** sent deployment configuration",
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Client ID", "value": client_id},
                                    {"title": "Environment", "value": deployment_data.get("client", {}).get("environment", "unknown")},
                                    {"title": "Webhooks", "value": "✅ Enabled" if deployment_data.get("features", {}).get("enable_webhooks") else "❌ Disabled"},
                                    {"title": "Autonomous", "value": "✅ Yes" if deployment_data.get("authentication", {}).get("webhook_auth") else "❌ No"},
                                    {"title": "Timestamp", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                                ]
                            }
                        ]
                    }
                }]
            }
            
            return await self._send_card(card, f"Deployment received from {client_id}")
        
        except Exception as e:
            logger.error(f"Error sending deployment notification: {e}")
            return False
    
    async def send_ready_package(self, client_id: str, credentials: Dict[str, Any]) -> bool:
        """
        Notify when ready package is sent back to client.
        
        Args:
            client_id: Client identifier
            credentials: Generated credentials
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            card = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "✅ Ready Package Sent",
                                "weight": "bolder",
                                "size": "large",
                                "color": "good"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"DRYAD sent ready package to **{client_id}**",
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Client ID", "value": client_id},
                                    {"title": "API Key", "value": credentials.get("api_key", "N/A")[:20] + "..."},
                                    {"title": "Webhook Secret", "value": "✅ Generated" if credentials.get("webhook_secret") else "❌ None"},
                                    {"title": "Status", "value": "🎯 Ready for client startup"},
                                    {"title": "Timestamp", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                                ]
                            },
                            {
                                "type": "TextBlock",
                                "text": "**Next Step:** Client should start webhook server and wait for instructions",
                                "wrap": True,
                                "color": "accent"
                            }
                        ]
                    }
                }]
            }
            
            return await self._send_card(card, f"Ready package sent to {client_id}")
        
        except Exception as e:
            logger.error(f"Error sending ready package notification: {e}")
            return False
    
    async def send_client_startup(self, client_id: str, webhook_url: str) -> bool:
        """
        Notify when client webhook server starts.
        
        Args:
            client_id: Client identifier
            webhook_url: Client's webhook URL
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            card = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "🚀 Client Webhook Server Started",
                                "weight": "bolder",
                                "size": "large",
                                "color": "good"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Client **{client_id}** is now listening for DRYAD instructions",
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Client ID", "value": client_id},
                                    {"title": "Webhook URL", "value": webhook_url},
                                    {"title": "Status", "value": "🎯 Ready to receive instructions"},
                                    {"title": "Timestamp", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                                ]
                            },
                            {
                                "type": "TextBlock",
                                "text": "**Bidirectional Communication Established!**",
                                "wrap": True,
                                "weight": "bolder",
                                "color": "good"
                            }
                        ]
                    }
                }]
            }
            
            return await self._send_card(card, f"Client {client_id} started")
        
        except Exception as e:
            logger.error(f"Error sending client startup notification: {e}")
            return False
    
    async def send_instruction_sent(self, client_id: str, instruction: Dict[str, Any]) -> bool:
        """
        Notify when DRYAD sends instruction to client.
        
        Args:
            client_id: Client identifier
            instruction: Instruction data
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            action = instruction.get("action", "unknown")
            endpoint = instruction.get("endpoint", "N/A")
            
            card = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "📤 Instruction Sent to Client",
                                "weight": "bolder",
                                "size": "medium",
                                "color": "accent"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"DRYAD → **{client_id}**",
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Client ID", "value": client_id},
                                    {"title": "Action", "value": action},
                                    {"title": "Endpoint", "value": endpoint},
                                    {"title": "Method", "value": instruction.get("method", "N/A")},
                                    {"title": "Timestamp", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                                ]
                            }
                        ]
                    }
                }]
            }
            
            return await self._send_card(card, f"Instruction sent to {client_id}")
        
        except Exception as e:
            logger.error(f"Error sending instruction notification: {e}")
            return False
    
    async def send_instruction_executed(self, client_id: str, instruction: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Notify when client executes instruction.
        
        Args:
            client_id: Client identifier
            instruction: Instruction that was executed
            result: Execution result
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            success = result.get("status") == "success"
            status_code = result.get("status_code", "N/A")
            
            card = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "✅ Instruction Executed" if success else "❌ Instruction Failed",
                                "weight": "bolder",
                                "size": "medium",
                                "color": "good" if success else "attention"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"**{client_id}** → DRYAD",
                                "wrap": True
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Client ID", "value": client_id},
                                    {"title": "Action", "value": instruction.get("action", "unknown")},
                                    {"title": "Status", "value": "✅ Success" if success else "❌ Failed"},
                                    {"title": "Status Code", "value": str(status_code)},
                                    {"title": "Timestamp", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                                ]
                            }
                        ]
                    }
                }]
            }
            
            return await self._send_card(card, f"Instruction executed by {client_id}")
        
        except Exception as e:
            logger.error(f"Error sending execution notification: {e}")
            return False
    
    async def _send_card(self, card: Dict[str, Any], log_message: str) -> bool:
        """Send Adaptive Card to Teams."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Teams notification sent: {log_message}")
                    return True
                else:
                    logger.error(f"Failed to send Teams notification: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending Teams card: {e}")
            return False


# Global instance
dryad_teams_notifier = DRYADTeamsNotifier()

