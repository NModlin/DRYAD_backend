# app/api/v1/endpoints/mcp.py
"""
Model Context Protocol (MCP) API endpoints for DRYAD.AI.
Provides standardized MCP interface for client applications.
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.core.security import get_client_context
from app.mcp.server import mcp_server, MCPRequest, MCPResponse, MCPNotification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])

@router.post("/", response_model=Dict[str, Any])
async def mcp_endpoint(
    request: Request,
    mcp_request: MCPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Main MCP endpoint for handling all MCP protocol messages.
    Supports initialize, list_resources, list_tools, call_tool, and other MCP methods.
    """
    try:
        # Get client context
        client_context = await get_client_context(request)
        if not client_context:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        method = mcp_request.method
        params = mcp_request.params or {}
        
        logger.info(f"MCP request: {method} from client {client_context.get('client_app_id', 'unknown')}")
        
        # Handle different MCP methods
        if method == "initialize":
            result = await mcp_server.handle_initialize(params)
        
        elif method == "resources/list":
            result = await mcp_server.handle_list_resources(client_context)
        
        elif method == "tools/list":
            result = await mcp_server.handle_list_tools(client_context)
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not tool_name:
                raise HTTPException(status_code=400, detail="Tool name required")
            result = await mcp_server.handle_call_tool(tool_name, arguments, client_context, db)
        
        elif method == "resources/read":
            uri = params.get("uri")
            if not uri:
                raise HTTPException(status_code=400, detail="Resource URI required")
            result = await handle_read_resource(uri, client_context, db)
        
        elif method == "notifications/initialized":
            # Client initialization complete
            result = {"acknowledged": True}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown MCP method: {method}")
        
        # Create MCP response
        response = MCPResponse(
            id=mcp_request.id,
            result=result
        )
        
        return response.model_dump(exclude_none=True)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        
        # Create error response
        error_response = MCPResponse(
            id=mcp_request.id,
            error={
                "code": -32603,  # Internal error
                "message": "Internal server error",
                "data": str(e) if logger.level <= logging.DEBUG else None
            }
        )
        
        return error_response.model_dump(exclude_none=True)


@router.get("/capabilities")
async def get_mcp_capabilities(request: Request):
    """Get MCP server capabilities and information."""
    try:
        client_context = await get_client_context(request)
        if not client_context:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": mcp_server.capabilities.model_dump(),
            "serverInfo": {
                "name": "DRYAD.AI MCP Server",
                "version": "1.0.0",
                "description": "Model Context Protocol server for DRYAD.AI Backend"
            },
            "resources": [r.model_dump() for r in mcp_server.resources],
            "tools": [t.model_dump() for t in mcp_server.tools]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MCP capabilities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notifications")
async def mcp_notifications(
    request: Request,
    notification: MCPNotification,
    db: AsyncSession = Depends(get_db)
):
    """Handle MCP notifications from clients."""
    try:
        client_context = await get_client_context(request)
        if not client_context:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        method = notification.method
        params = notification.params or {}
        
        logger.info(f"MCP notification: {method} from client {client_context.get('client_app_id', 'unknown')}")
        
        # Handle different notification types
        if method == "notifications/cancelled":
            # Request cancellation
            request_id = params.get("requestId")
            logger.info(f"Request cancelled: {request_id}")
        
        elif method == "notifications/progress":
            # Progress update
            progress = params.get("progress", {})
            logger.debug(f"Progress update: {progress}")
        
        else:
            logger.warning(f"Unknown MCP notification: {method}")
        
        return {"acknowledged": True}
    
    except Exception as e:
        logger.error(f"MCP notification failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_read_resource(uri: str, client_context: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Handle reading a specific MCP resource."""
    try:
        if uri == "DRYAD.AI://documents":
            # Return user's documents from database and vector store
            user_id = client_context.get("user_id")
            client_app_id = client_context.get("client_app_id")

            if not user_id:
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": '{"error": "User authentication required"}'
                        }
                    ]
                }

            # Get documents from database
            from app.database.models import Document
            from sqlalchemy import select

            stmt = select(Document).where(
                Document.user_id == user_id,
                Document.is_active == True
            ).order_by(Document.created_at.desc()).limit(50)

            result = await db.execute(stmt)
            documents = result.scalars().all()

            # Format documents for MCP response
            document_data = []
            for doc in documents:
                document_data.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "content_type": doc.content_type,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat(),
                    "tags": doc.tags or [],
                    "metadata": doc.metadata or {}
                })

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "total_documents": len(document_data),
                            "documents": document_data,
                            "user_id": user_id,
                            "client_app_id": client_app_id
                        }, indent=2)
                    }
                ]
            }
        
        elif uri == "DRYAD.AI://conversations":
            # Return conversation history from database
            user_id = client_context.get("user_id")
            client_app_id = client_context.get("client_app_id")

            if not user_id:
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": '{"error": "User authentication required"}'
                        }
                    ]
                }

            # Get conversation history from database
            from app.database.models import ChatHistory
            from sqlalchemy import select

            stmt = select(ChatHistory).where(
                ChatHistory.user_id == user_id
            ).order_by(ChatHistory.created_at.desc()).limit(100)

            if client_app_id:
                stmt = stmt.where(ChatHistory.client_app_id == client_app_id)

            result = await db.execute(stmt)
            conversations = result.scalars().all()

            # Format conversations for MCP response
            conversation_data = []
            for chat in conversations:
                conversation_data.append({
                    "id": str(chat.id),
                    "user_message": chat.user_message,
                    "ai_response": chat.ai_response,
                    "context_scope": chat.context_scope,
                    "model_used": chat.model_used,
                    "created_at": chat.created_at.isoformat(),
                    "client_app_id": chat.client_app_id,
                    "metadata": chat.metadata or {}
                })

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "total_conversations": len(conversation_data),
                            "conversations": conversation_data,
                            "user_id": user_id,
                            "client_app_id": client_app_id
                        }, indent=2)
                    }
                ]
            }
        
        elif uri == "DRYAD.AI://knowledge":
            # Return shared knowledge from cross-client learning
            user_id = client_context.get("user_id")
            client_app_id = client_context.get("client_app_id")

            if not user_id:
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": '{"error": "User authentication required"}'
                        }
                    ]
                }

            # Get shared knowledge from database
            from app.database.models import SharedKnowledge
            from sqlalchemy import select

            stmt = select(SharedKnowledge).where(
                SharedKnowledge.is_active == True
            ).order_by(SharedKnowledge.confidence_score.desc()).limit(50)

            result = await db.execute(stmt)
            shared_insights = result.scalars().all()

            # Format shared knowledge for MCP response
            knowledge_data = []
            for insight in shared_insights:
                knowledge_data.append({
                    "id": str(insight.id),
                    "insight_text": insight.insight_text,
                    "insight_type": insight.insight_type,
                    "confidence_score": float(insight.confidence_score),
                    "usage_count": insight.usage_count,
                    "source_interactions": insight.source_interactions,
                    "created_at": insight.created_at.isoformat(),
                    "updated_at": insight.updated_at.isoformat(),
                    "tags": insight.tags or [],
                    "metadata": insight.metadata or {}
                })

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "total_insights": len(knowledge_data),
                            "shared_knowledge": knowledge_data,
                            "user_id": user_id,
                            "client_app_id": client_app_id,
                            "description": "Cross-client learning insights and shared knowledge patterns"
                        }, indent=2)
                    }
                ]
            }
        
        elif uri == "DRYAD.AI://analytics":
            # Return usage analytics and monitoring data
            user_id = client_context.get("user_id")
            client_app_id = client_context.get("client_app_id")

            if not user_id:
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": '{"error": "User authentication required"}'
                        }
                    ]
                }

            # Get analytics data from various sources
            from app.database.models import ChatHistory, Document
            from sqlalchemy import select, func
            from datetime import datetime, timedelta

            # Calculate time ranges
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            last_30d = now - timedelta(days=30)

            # Chat analytics
            chat_24h = await db.execute(
                select(func.count(ChatHistory.id)).where(
                    ChatHistory.user_id == user_id,
                    ChatHistory.created_at >= last_24h
                )
            )
            chat_7d = await db.execute(
                select(func.count(ChatHistory.id)).where(
                    ChatHistory.user_id == user_id,
                    ChatHistory.created_at >= last_7d
                )
            )
            chat_30d = await db.execute(
                select(func.count(ChatHistory.id)).where(
                    ChatHistory.user_id == user_id,
                    ChatHistory.created_at >= last_30d
                )
            )

            # Document analytics
            doc_count = await db.execute(
                select(func.count(Document.id)).where(
                    Document.user_id == user_id,
                    Document.is_active == True
                )
            )
            doc_size = await db.execute(
                select(func.sum(Document.file_size)).where(
                    Document.user_id == user_id,
                    Document.is_active == True
                )
            )

            # Model usage analytics
            model_usage = await db.execute(
                select(ChatHistory.model_used, func.count(ChatHistory.id)).where(
                    ChatHistory.user_id == user_id,
                    ChatHistory.created_at >= last_30d
                ).group_by(ChatHistory.model_used)
            )

            analytics_data = {
                "user_id": user_id,
                "client_app_id": client_app_id,
                "generated_at": now.isoformat(),
                "chat_analytics": {
                    "conversations_24h": chat_24h.scalar() or 0,
                    "conversations_7d": chat_7d.scalar() or 0,
                    "conversations_30d": chat_30d.scalar() or 0
                },
                "document_analytics": {
                    "total_documents": doc_count.scalar() or 0,
                    "total_storage_bytes": doc_size.scalar() or 0,
                    "total_storage_mb": round((doc_size.scalar() or 0) / (1024 * 1024), 2)
                },
                "model_usage": {
                    row[0]: row[1] for row in model_usage.fetchall()
                },
                "time_ranges": {
                    "last_24h": last_24h.isoformat(),
                    "last_7d": last_7d.isoformat(),
                    "last_30d": last_30d.isoformat()
                }
            }

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(analytics_data, indent=2)
                    }
                ]
            }
        
        else:
            raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read resource {uri}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read resource")


@router.get("/health")
async def mcp_health_check():
    """MCP server health check endpoint."""
    return {
        "status": "healthy",
        "protocol_version": "2025-06-18",
        "server": "DRYAD.AI MCP Server",
        "timestamp": "2025-09-25T12:00:00Z"
    }
