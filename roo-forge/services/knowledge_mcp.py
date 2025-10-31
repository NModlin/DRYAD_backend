"""
Knowledge Trees MCP Server for ROO-Forge

Integrates with DRYAD Knowledge Tree System for GAD project management,
quantum branching, and persistent learning. Supports all GAD layers
through knowledge persistence and context sharing.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_mcp import BaseMCPServer

logger = logging.getLogger(__name__)


class KnowledgeMCPServer(BaseMCPServer):
    """
    MCP Server for DRYAD Knowledge Tree System integration.
    
    Provides GAD project organization, knowledge persistence, and
    quantum branching capabilities through DRYAD's Knowledge Tree API.
    """
    
    def __init__(self):
        super().__init__(
            name="knowledge_trees",
            description="DRYAD Knowledge Tree System integration for GAD project management and learning"
        )
        
    async def _list_tools(self):
        """List Knowledge Trees MCP tools"""
        return [
            {
                "name": "create_gad_grove",
                "description": "Create a new knowledge grove for GAD project organization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string", "description": "GAD project name"},
                        "description": {"type": "string", "description": "Project description"},
                        "owner": {"type": "string", "description": "Project owner/agent name"},
                        "gad_hierarchy": {"type": "object", "description": "GAD agent hierarchy configuration"}
                    },
                    "required": ["project_name", "description", "owner"]
                }
            },
            {
                "name": "create_gad_branch",
                "description": "Create a new branch for GAD phase or exploration path",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grove_id": {"type": "string", "description": "Grove ID"},
                        "branch_name": {"type": "string", "description": "Branch name"},
                        "phase": {"type": "string", "enum": ["plan", "review", "execute", "remember"], "description": "GAD lifecycle phase"},
                        "parent_branch_id": {"type": "string", "description": "Parent branch ID for quantum branching"},
                        "priority": {"type": "integer", "description": "Branch priority", "default": 1}
                    },
                    "required": ["grove_id", "branch_name", "phase"]
                }
            },
            {
                "name": "create_vessel",
                "description": "Create a vessel for storing GAD outputs and context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "branch_id": {"type": "string", "description": "Branch ID"},
                        "vessel_name": {"type": "string", "description": "Vessel name"},
                        "vessel_type": {"type": "string", "description": "Type of content (plan, code, review, learning)"},
                        "content": {"type": "string", "description": "Initial content"},
                        "context_data": {"type": "object", "description": "Additional context data"}
                    },
                    "required": ["branch_id", "vessel_name", "vessel_type"]
                }
            },
            {
                "name": "update_vessel",
                "description": "Update vessel content with GAD outputs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vessel_id": {"type": "string", "description": "Vessel ID"},
                        "content": {"type": "string", "description": "Updated content"},
                        "update_type": {"type": "string", "description": "Type of update (append, replace, merge)"},
                        "author": {"type": "string", "description": "Updating agent name"}
                    },
                    "required": ["vessel_id", "content"]
                }
            },
            {
                "name": "consult_oracle",
                "description": "Consult DRYAD oracle for GAD guidance and decisions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "Question for the oracle"},
                        "context": {"type": "object", "description": "Current context (branch, vessel, phase)"},
                        "gad_role": {"type": "string", "description": "GAD role asking the question"},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high"], "description": "Question urgency", "default": "medium"}
                    },
                    "required": ["question", "gad_role"]
                }
            },
            {
                "name": "get_project_context",
                "description": "Get complete project context from knowledge tree",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grove_id": {"type": "string", "description": "Grove ID"},
                        "include_vessels": {"type": "boolean", "description": "Include vessel contents", "default": True},
                        "phase_filter": {"type": "string", "description": "Filter by GAD phase"}
                    },
                    "required": ["grove_id"]
                }
            }
        ]
        
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Knowledge Trees tool execution"""
        
        if name == "create_gad_grove":
            return await self._create_gad_grove(arguments)
        elif name == "create_gad_branch":
            return await self._create_gad_branch(arguments)
        elif name == "create_vessel":
            return await self._create_vessel(arguments)
        elif name == "update_vessel":
            return await self._update_vessel(arguments)
        elif name == "consult_oracle":
            return await self._consult_oracle(arguments)
        elif name == "get_project_context":
            return await self._get_project_context(arguments)
        else:
            return {"status": "error", "message": f"Unknown tool: {name}"}
            
    async def _create_gad_grove(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new GAD project grove"""
        try:
            grove_data = {
                "name": args["project_name"],
                "description": args["description"],
                "owner": args["owner"],
                "type": "gad_project",
                "metadata": {
                    "gad_hierarchy": args.get("gad_hierarchy", {}),
                    "created_by": "gad_system",
                    "project_type": "gad_development",
                    "phase": "planning"
                }
            }
            
            result = await self.dryad_request("POST", "/api/v1/dryad/groves", data=grove_data)
            
            # Create default GAD branches
            await self._create_default_gad_branches(result["id"])
            
            return {
                "status": "success",
                "grove_id": result["id"],
                "grove_name": result["name"],
                "message": f"GAD grove '{result['name']}' created with default branch structure"
            }
            
        except Exception as e:
            logger.error(f"Create GAD grove failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _create_gad_branch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new GAD branch"""
        try:
            branch_data = {
                "grove_id": args["grove_id"],
                "name": args["branch_name"],
                "description": f"GAD {args['phase']} phase branch",
                "branch_type": "gad_phase",
                "status": "active",
                "priority": args.get("priority", 1),
                "parent_id": args.get("parent_branch_id"),
                "metadata": {
                    "gad_phase": args["phase"],
                    "created_by": "gad_system",
                    "quantum_branch": args.get("parent_branch_id") is not None
                }
            }
            
            result = await self.dryad_request("POST", "/api/v1/dryad/branches", data=branch_data)
            
            return {
                "status": "success",
                "branch_id": result["id"],
                "branch_name": result["name"],
                "gad_phase": args["phase"],
                "parent_branch_id": args.get("parent_branch_id"),
                "message": f"GAD branch '{result['name']}' created for {args['phase']} phase"
            }
            
        except Exception as e:
            logger.error(f"Create GAD branch failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _create_vessel(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vessel for GAD content"""
        try:
            vessel_data = {
                "branch_id": args["branch_id"],
                "name": args["vessel_name"],
                "content": args.get("content", ""),
                "vessel_type": args["vessel_type"],
                "metadata": {
                    "gad_content_type": args["vessel_type"],
                    "created_by": "gad_system",
                    "context_data": args.get("context_data", {}),
                    "phase": self._infer_phase_from_type(args["vessel_type"])
                }
            }
            
            result = await self.dryad_request("POST", "/api/v1/dryad/vessels", data=vessel_data)
            
            return {
                "status": "success",
                "vessel_id": result["id"],
                "vessel_name": result["name"],
                "vessel_type": args["vessel_type"],
                "branch_id": args["branch_id"],
                "message": f"Vessel '{result['name']}' created for {args['vessel_type']} content"
            }
            
        except Exception as e:
            logger.error(f"Create vessel failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _update_vessel(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update vessel content"""
        try:
            vessel_id = args["vessel_id"]
            
            # Get current vessel content
            current = await self.dryad_request("GET", f"/api/v1/dryad/vessels/{vessel_id}")
            
            # Apply update based on type
            new_content = args["content"]
            update_type = args.get("update_type", "replace")
            
            if update_type == "append":
                new_content = current["content"] + "\n\n" + args["content"]
            elif update_type == "merge":
                new_content = self._merge_content(current["content"], args["content"])
                
            update_data = {
                "content": new_content,
                "metadata": {
                    **current["metadata"],
                    "last_updated_by": args.get("author", "gad_agent"),
                    "update_type": update_type,
                    "updated_at": "now"
                }
            }
            
            result = await self.dryad_request("PUT", f"/api/v1/dryad/vessels/{vessel_id}", data=update_data)
            
            return {
                "status": "success",
                "vessel_id": vessel_id,
                "update_type": update_type,
                "updated_by": args.get("author"),
                "message": f"Vessel updated with {update_type} operation"
            }
            
        except Exception as e:
            logger.error(f"Update vessel failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _consult_oracle(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Consult DRYAD oracle for guidance"""
        try:
            oracle_data = {
                "question": args["question"],
                "context": args.get("context", {}),
                "requesting_agent": args["gad_role"],
                "urgency": args.get("urgency", "medium"),
                "consultation_type": "gad_guidance"
            }
            
            result = await self.dryad_request("POST", "/api/v1/dryad/oracle/consult", data=oracle_data)
            
            return {
                "status": "success",
                "question": args["question"],
                "gad_role": args["gad_role"],
                "oracle_response": result.get("response", ""),
                "confidence": result.get("confidence", 0),
                "suggestions": result.get("suggestions", []),
                "message": f"Oracle consulted for {args['gad_role']} guidance"
            }
            
        except Exception as e:
            logger.error(f"Consult oracle failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _get_project_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete project context"""
        try:
            grove_id = args["grove_id"]
            
            # Get grove details
            grove = await self.dryad_request("GET", f"/api/v1/dryad/groves/{grove_id}")
            
            # Get branches
            branches = await self.dryad_request(
                "GET", 
                f"/api/v1/dryad/groves/{grove_id}/branches",
                params={"include_inactive": False}
            )
            
            # Filter by phase if specified
            if args.get("phase_filter"):
                branches = [b for b in branches if b["metadata"].get("gad_phase") == args["phase_filter"]]
                
            # Get vessels if requested
            vessels = []
            if args.get("include_vessels", True):
                for branch in branches:
                    branch_vessels = await self.dryad_request(
                        "GET", 
                        f"/api/v1/dryad/branches/{branch['id']}/vessels"
                    )
                    vessels.extend(branch_vessels)
            
            return {
                "status": "success",
                "grove": grove,
                "branches": branches,
                "vessels": vessels,
                "phase_filter": args.get("phase_filter"),
                "context_summary": {
                    "total_branches": len(branches),
                    "total_vessels": len(vessels),
                    "active_phases": list(set(b["metadata"].get("gad_phase") for b in branches)),
                    "project_progress": self._calculate_project_progress(branches, vessels)
                }
            }
            
        except Exception as e:
            logger.error(f"Get project context failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _create_default_gad_branches(self, grove_id: str):
        """Create default GAD branch structure"""
        default_branches = [
            {"name": "Planning Phase", "phase": "plan"},
            {"name": "Review Phase", "phase": "review"},
            {"name": "Execution Phase", "phase": "execute"},
            {"name": "Memory Phase", "phase": "remember"}
        ]
        
        for branch in default_branches:
            try:
                await self._create_gad_branch({
                    "grove_id": grove_id,
                    "branch_name": branch["name"],
                    "phase": branch["phase"]
                })
            except Exception as e:
                logger.warning(f"Failed to create default branch {branch['name']}: {e}")
                
    def _infer_phase_from_type(self, vessel_type: str) -> str:
        """Infer GAD phase from vessel type"""
        phase_mapping = {
            "plan": "plan",
            "requirements": "plan",
            "specification": "plan",
            "code": "execute",
            "implementation": "execute",
            "test": "execute",
            "review": "review",
            "security": "review",
            "approval": "review",
            "learning": "remember",
            "pattern": "remember",
            "best_practice": "remember"
        }
        return phase_mapping.get(vessel_type, "general")
        
    def _merge_content(self, current: str, new: str) -> str:
        """Merge new content with existing content"""
        return current + "\n\n" + new
        
    def _calculate_project_progress(self, branches: List[Dict], vessels: List[Dict]) -> Dict[str, Any]:
        """Calculate project progress from branches and vessels"""
        phases = ["plan", "review", "execute", "remember"]
        progress = {}
        
        for phase in phases:
            phase_branches = [b for b in branches if b["metadata"].get("gad_phase") == phase]
            phase_vessels = [v for v in vessels if v["metadata"].get("phase") == phase]
            
            progress[phase] = {
                "branches": len(phase_branches),
                "vessels": len(phase_vessels),
                "status": "active" if phase_branches else "pending"
            }
            
        return progress


# Main entry point for MCP server
if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = KnowledgeMCPServer()
        async with server:
            app = server.get_app()
            await app.run()
    
    asyncio.run(main())