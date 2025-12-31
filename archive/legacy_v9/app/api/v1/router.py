"""
DRYAD.AI API Router for Version 1

This module consolidates all API endpoints for the DRYAD.AI system,
including the Agentic University System (Level 6).
"""

from fastapi import APIRouter

# Import all endpoint routers
from app.api.v1.endpoints.universities import router as universities_router
from app.api.v1.endpoints.curriculum import router as curriculum_router
from app.api.v1.endpoints.competitions import router as competitions_router
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.agent_registry import router as agent_registry_router
from app.api.v1.endpoints.enhanced_university import router as enhanced_university_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.dryad import router as dryad_router
from app.api.v1.endpoints.docs import router as docs_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.mcp import router as mcp_router
from app.api.v1.endpoints.memory import router as memory_router
from app.api.v1.endpoints.websocket import router as websocket_router
from app.api.v1.endpoints.self_healing import router as self_healing_router
from app.api.v1.endpoints.guardrails import router as guardrails_router
from app.api.v1.endpoints.hitl_approvals import router as hitl_approvals_router
from app.api.v1.endpoints.logging import router as logging_router
from app.api.v1.endpoints.sandbox import router as sandbox_router
from app.api.v1.endpoints.scribe import router as scribe_router
from app.api.v1.endpoints.radar import router as radar_router
from app.api.v1.endpoints.realtime import router as realtime_router
from app.api.v1.endpoints.skill_trees import router as skill_trees_router
from app.api.v1.endpoints.skill_progress import router as skill_progress_router
from app.api.v1.endpoints.specializations import router as specializations_router
from app.api.v1.endpoints.progression_paths import router as progression_paths_router
from app.api.v1.endpoints.orchestrator import router as orchestrator_router
from app.api.v1.endpoints.multi_agent import router as multi_agent_router
from app.api.v1.endpoints.multimodal import router as multimodal_router
from app.api.v1.endpoints.ai_workflows import router as ai_workflows_router
from app.api.v1.endpoints.api_keys import router as api_keys_router
from app.api.v1.endpoints.agent_studio import router as agent_studio_router
from app.api.v1.endpoints.agent_enhancements import router as agent_enhancements_router
from app.api.v1.endpoints.collaboration import router as collaboration_router
from app.api.v1.endpoints.code_editor import router as code_editor_router
from app.api.v1.endpoints.codebase_analyst import router as codebase_analyst_router
from app.api.v1.endpoints.deployment_integration import router as deployment_integration_router
from app.api.v1.endpoints.developer_portal import router as developer_portal_router
from app.api.v1.endpoints.project_manager import router as project_manager_router
from app.api.v1.endpoints.security_dashboard import router as security_dashboard_router
from app.api.v1.endpoints.self_healing_ui import router as self_healing_ui_router
from app.api.v1.endpoints.test_engineer import router as test_engineer_router
from app.api.v1.endpoints.tool_registry import router as tool_registry_router
from app.api.v1.endpoints.workflows import router as workflows_router
from app.api.v1.endpoints.chat_history import router as chat_history_router
from app.api.v1.endpoints.admin import router as admin_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(docs_router, prefix="/docs", tags=["Documentation"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(mcp_router, prefix="/mcp", tags=["MCP"])
api_router.include_router(memory_router, prefix="/memory", tags=["Memory"])
api_router.include_router(websocket_router, prefix="/websocket", tags=["WebSocket"])
api_router.include_router(self_healing_router, prefix="/self-healing", tags=["Self Healing"])
api_router.include_router(guardrails_router, prefix="/guardrails", tags=["Guardrails"])
api_router.include_router(hitl_approvals_router, prefix="/approvals", tags=["HITL Approvals"])
api_router.include_router(logging_router, prefix="/logs", tags=["Logging"])
api_router.include_router(sandbox_router, prefix="/sandbox", tags=["Sandbox"])
api_router.include_router(scribe_router, prefix="/scribe", tags=["Scribe"])
api_router.include_router(radar_router, prefix="/radar", tags=["Radar"])
api_router.include_router(realtime_router, prefix="/realtime", tags=["Real-time"])
api_router.include_router(skill_trees_router, prefix="/skill-trees", tags=["Skill Trees"])
api_router.include_router(skill_progress_router, prefix="/skill-progress", tags=["Skill Progress"])
api_router.include_router(specializations_router, prefix="/specializations", tags=["Specializations"])
api_router.include_router(progression_paths_router, prefix="/progression-paths", tags=["Progression Paths"])
api_router.include_router(orchestrator_router, prefix="/orchestrator", tags=["Orchestrator"])
api_router.include_router(multi_agent_router, prefix="/multi-agent", tags=["Multi-Agent"])
api_router.include_router(multimodal_router, prefix="/multimodal", tags=["Multimodal"])
api_router.include_router(ai_workflows_router, prefix="/ai-workflows", tags=["AI Workflows"])
api_router.include_router(api_keys_router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(agent_studio_router, prefix="/agent-studio", tags=["Agent Studio"])
api_router.include_router(agent_enhancements_router, prefix="/agent-enhancements", tags=["Agent Enhancements"])
api_router.include_router(collaboration_router, prefix="/collaboration", tags=["Collaboration"])
api_router.include_router(code_editor_router, prefix="/code-editor", tags=["Code Editor"])
api_router.include_router(codebase_analyst_router, prefix="/codebase-analyst", tags=["Codebase Analyst"])
api_router.include_router(deployment_integration_router, prefix="/deployment", tags=["Deployment"])
api_router.include_router(developer_portal_router, prefix="/developer-portal", tags=["Developer Portal"])
api_router.include_router(project_manager_router, prefix="/project-manager", tags=["Project Manager"])
api_router.include_router(security_dashboard_router, prefix="/security-dashboard", tags=["Security Dashboard"])
api_router.include_router(self_healing_ui_router, prefix="/self-healing-ui", tags=["Self Healing UI"])
api_router.include_router(test_engineer_router, prefix="/test-engineer", tags=["Test Engineer"])
api_router.include_router(tool_registry_router, prefix="/tool-registry", tags=["Tool Registry"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(chat_history_router, prefix="/chat-history", tags=["Chat History"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

# Agentic University System (Level 6) endpoints
api_router.include_router(universities_router, prefix="/universities", tags=["Universities"])
api_router.include_router(curriculum_router, prefix="/curriculum", tags=["Curriculum"])
api_router.include_router(competitions_router, prefix="/competitions", tags=["Competitions"])
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(agent_registry_router, prefix="/agent-registry", tags=["Agent Registry"])
api_router.include_router(enhanced_university_router, prefix="/enhanced-university", tags=["Enhanced University"])

# Core DRYAD endpoints
api_router.include_router(dryad_router, prefix="/dryad", tags=["DRYAD"])

# Export the main API router
__all__ = ["api_router"]