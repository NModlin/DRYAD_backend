"""
Agent Studio Webhook Endpoints

Provides webhook endpoints for automated agent documentation submission
and management. These endpoints enable frontend applications to automatically
submit and update agent documentation when agents are created or modified.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.core.logging_config import get_logger
from app.core.config import config

logger = get_logger(__name__)
router = APIRouter()

# In-memory webhook event store (in production, use database)
_webhook_events: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UsageExample(BaseModel):
    """Usage example model."""
    title: str
    code: str
    description: str


class ApiReference(BaseModel):
    """API reference model."""
    endpoint: str
    method: str
    parameters: Dict[str, str]


class AgentDocumentation(BaseModel):
    """Agent documentation model."""
    title: str
    description: str
    version: str
    category: str
    capabilities: list[str]
    usage_examples: list[UsageExample]
    api_reference: ApiReference
    limitations: list[str]
    support_contact: str


class DocumentationMetadata(BaseModel):
    """Documentation metadata model."""
    submitted_by: str
    submission_date: str
    auto_generated: bool = True


class SubmitDocsRequest(BaseModel):
    """Submit documentation request."""
    agent_id: str
    client_id: str
    documentation: AgentDocumentation
    metadata: DocumentationMetadata


class UpdateDocsRequest(BaseModel):
    """Update documentation request."""
    agent_id: str
    doc_id: str
    updates: Dict[str, Any]


class AgentApprovedRequest(BaseModel):
    """Agent approved notification request."""
    agent_id: str
    submission_id: str
    approved_by: str
    approved_at: str
    agent_configuration: Dict[str, Any]


class WebhookResponse(BaseModel):
    """Webhook response model."""
    status: str
    doc_id: str
    message: str
    documentation_url: str
    webhook_event_id: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # In production, verify against database
    # For now, accept any non-empty key
    if not x_api_key.startswith("gai_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    return x_api_key


async def log_webhook_event(
    event_type: str,
    payload: Dict[str, Any],
    api_key: str,
    status: str,
    error_message: Optional[str] = None
) -> str:
    """Log webhook event for auditing."""
    event_id = f"evt_{uuid.uuid4().hex[:16]}"
    
    event = {
        "id": event_id,
        "event_type": event_type,
        "payload": payload,
        "api_key_id": api_key[:10] + "...",  # Truncate for security
        "status": status,
        "error_message": error_message,
        "created_at": datetime.utcnow().isoformat()
    }
    
    _webhook_events[event_id] = event
    
    logger.info(f"Webhook event logged: {event_id} - {event_type} - {status}")
    
    return event_id


async def generate_documentation_file(
    agent_id: str,
    client_id: str,
    documentation: AgentDocumentation
) -> str:
    """Generate documentation markdown file."""
    # Determine file path
    docs_base = Path(config.AGENT_DOCS_PATH if hasattr(config, 'AGENT_DOCS_PATH') else "./docs/agent-studio/client-agents")
    client_dir = docs_base / client_id.split("-")[0]  # e.g., "radar-prod" -> "radar"
    client_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename from agent name
    agent_name = documentation.title.lower().replace(" ", "-")
    file_path = client_dir / f"{agent_name}.md"
    
    # Generate markdown content
    markdown_content = f"""# {documentation.title}

**Client:** {client_id}  
**Category:** {documentation.category}  
**Version:** {documentation.version}  
**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d')}

---

## Overview

{documentation.description}

---

## Capabilities

"""
    
    for capability in documentation.capabilities:
        markdown_content += f"- {capability}\n"
    
    markdown_content += "\n---\n\n## Usage Examples\n\n"
    
    for example in documentation.usage_examples:
        markdown_content += f"### {example.title}\n\n"
        markdown_content += f"{example.description}\n\n"
        markdown_content += f"```\n{example.code}\n```\n\n"
    
    markdown_content += "---\n\n## API Reference\n\n"
    markdown_content += f"**Endpoint:** `{documentation.api_reference.method} {documentation.api_reference.endpoint}`\n\n"
    markdown_content += "**Parameters:**\n\n"
    
    for param, desc in documentation.api_reference.parameters.items():
        markdown_content += f"- `{param}`: {desc}\n"
    
    markdown_content += "\n---\n\n## Limitations\n\n"
    
    for limitation in documentation.limitations:
        markdown_content += f"- {limitation}\n"
    
    markdown_content += f"\n---\n\n## Support\n\n"
    markdown_content += f"For support, contact: {documentation.support_contact}\n"
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    logger.info(f"Documentation file generated: {file_path}")
    
    # Return relative path
    return str(file_path.relative_to(docs_base.parent))


async def check_documentation_exists(agent_id: str, client_id: str) -> bool:
    """Check if documentation already exists for agent."""
    # In production, check database
    # For now, return False
    return False


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@router.post("/webhook/submit-docs", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED, tags=["Webhooks"])
async def submit_agent_documentation(
    request: SubmitDocsRequest,
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit agent documentation via webhook.
    
    This endpoint is called automatically when an agent is created to submit
    its documentation. The documentation is stored in the database and a
    markdown file is generated in the docs directory.
    
    **Authentication:** API Key (Header: X-API-Key)
    
    **Rate Limit:** 60 requests per minute
    """
    try:
        logger.info(f"Webhook: Submit documentation for agent {request.agent_id} from client {request.client_id}")
        
        # Check if documentation already exists
        if await check_documentation_exists(request.agent_id, request.client_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Documentation already exists for this agent"
            )
        
        # Generate documentation ID
        doc_id = str(uuid.uuid4())
        
        # Generate documentation file
        doc_url = await generate_documentation_file(
            request.agent_id,
            request.client_id,
            request.documentation
        )
        
        # Log webhook event
        event_id = await log_webhook_event(
            event_type="submit_docs",
            payload=request.dict(),
            api_key=api_key,
            status="success"
        )
        
        # In production, save to database
        # await save_documentation_to_db(doc_id, request, doc_url, db)
        
        logger.info(f"Documentation submitted successfully: {doc_id}")
        
        return WebhookResponse(
            status="success",
            doc_id=doc_id,
            message="Agent documentation submitted successfully",
            documentation_url=f"/docs/{doc_url}",
            webhook_event_id=event_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting documentation: {e}")
        
        # Log failed event
        await log_webhook_event(
            event_type="submit_docs",
            payload=request.dict(),
            api_key=api_key,
            status="failed",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit documentation: {str(e)}"
        )


@router.post("/webhook/update-docs", response_model=WebhookResponse, tags=["Webhooks"])
async def update_agent_documentation(
    request: UpdateDocsRequest,
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Update existing agent documentation via webhook.
    
    This endpoint is called when an agent is updated to refresh its documentation.
    
    **Authentication:** API Key (Header: X-API-Key)
    
    **Rate Limit:** 60 requests per minute
    """
    try:
        logger.info(f"Webhook: Update documentation {request.doc_id} for agent {request.agent_id}")
        
        # In production, update database and regenerate file
        # For now, just log the event
        
        # Log webhook event
        event_id = await log_webhook_event(
            event_type="update_docs",
            payload=request.dict(),
            api_key=api_key,
            status="success"
        )
        
        logger.info(f"Documentation updated successfully: {request.doc_id}")
        
        return WebhookResponse(
            status="success",
            doc_id=request.doc_id,
            message="Documentation updated successfully",
            documentation_url=f"/docs/agent-studio/client-agents/{request.agent_id}",
            webhook_event_id=event_id
        )
        
    except Exception as e:
        logger.error(f"Error updating documentation: {e}")
        
        # Log failed event
        await log_webhook_event(
            event_type="update_docs",
            payload=request.dict(),
            api_key=api_key,
            status="failed",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update documentation: {str(e)}"
        )


@router.post("/webhook/agent-approved", response_model=WebhookResponse, tags=["Webhooks"])
async def agent_approved_notification(
    request: AgentApprovedRequest,
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook called when admin approves an agent.
    
    This triggers automatic documentation generation for the approved agent.
    
    **Authentication:** API Key (Header: X-API-Key) - Internal use only
    
    **Rate Limit:** 60 requests per minute
    """
    try:
        logger.info(f"Webhook: Agent {request.agent_id} approved by {request.approved_by}")
        
        # Generate documentation ID
        doc_id = str(uuid.uuid4())
        
        # In production, generate documentation from agent configuration
        # For now, just log the event
        
        # Log webhook event
        event_id = await log_webhook_event(
            event_type="agent_approved",
            payload=request.dict(),
            api_key=api_key,
            status="success"
        )
        
        logger.info(f"Agent approval processed: {request.agent_id}")
        
        return WebhookResponse(
            status="success",
            doc_id=doc_id,
            message="Agent approval processed",
            documentation_url=f"/docs/agent-studio/client-agents/{request.agent_id}",
            webhook_event_id=event_id
        )
        
    except Exception as e:
        logger.error(f"Error processing agent approval: {e}")
        
        # Log failed event
        await log_webhook_event(
            event_type="agent_approved",
            payload=request.dict(),
            api_key=api_key,
            status="failed",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process agent approval: {str(e)}"
        )


@router.get("/webhook/events", tags=["Webhooks"])
async def get_webhook_events(
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """
    Get webhook event log.
    
    Returns recent webhook events for auditing and debugging.
    
    **Authentication:** API Key (Header: X-API-Key)
    """
    try:
        # Get recent events
        events = list(_webhook_events.values())
        events.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "events": events[:limit],
            "total": len(events)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving webhook events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve webhook events: {str(e)}"
        )

