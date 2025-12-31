"""
University MCP Server for ROO-Forge

Integrates with DRYAD University System for GAD agent training, curriculum management,
and university governance. Supports the Human Provost (Layer 4) and Forest Keeper (Layer 3) roles.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_mcp import BaseMCPServer

logger = logging.getLogger(__name__)


class UniversityMCPServer(BaseMCPServer):
    """
    MCP Server for DRYAD University System integration.
    
    Provides GAD agent training, curriculum management, and university oversight
    capabilities through DRYAD's University API.
    """
    
    def __init__(self):
        super().__init__(
            name="dryad_university",
            description="DRYAD University System integration for GAD agent training and governance"
        )
        
    async def _list_tools(self):
        """List University MCP tools"""
        return [
            {
                "name": "create_university",
                "description": "Create a new university instance for GAD agent training",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "University name"},
                        "description": {"type": "string", "description": "University description"},
                        "specialization": {"type": "string", "description": "Primary specialization focus"},
                        "max_agents": {"type": "integer", "description": "Maximum number of agents", "default": 100}
                    },
                    "required": ["name", "description"]
                }
            },
            {
                "name": "get_university_status",
                "description": "Get status and statistics for a university",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "university_id": {"type": "string", "description": "University ID"}
                    },
                    "required": ["university_id"]
                }
            },
            {
                "name": "enroll_gad_agent",
                "description": "Enroll a GAD agent in university curriculum",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "university_id": {"type": "string", "description": "University ID"},
                        "agent_name": {"type": "string", "description": "Agent name"},
                        "role": {"type": "string", "description": "GAD role (forest-keeper, guardian-reviewer, branch-weaver, human-provost)"},
                        "curriculum_id": {"type": "string", "description": "Curriculum to enroll in"}
                    },
                    "required": ["university_id", "agent_name", "role"]
                }
            },
            {
                "name": "create_gad_curriculum",
                "description": "Create GAD-specific curriculum for agent training",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Curriculum name"},
                        "description": {"type": "string", "description": "Curriculum description"},
                        "gad_role": {"type": "string", "description": "Target GAD role"},
                        "courses": {"type": "array", "items": {"type": "string"}, "description": "Course IDs"}
                    },
                    "required": ["name", "description", "gad_role"]
                }
            },
            {
                "name": "get_agent_progress",
                "description": "Get GAD agent training progress and performance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string", "description": "Agent name"},
                        "university_id": {"type": "string", "description": "University ID"}
                    },
                    "required": ["agent_name"]
                }
            },
            {
                "name": "approve_agent_decision",
                "description": "Approve or reject GAD agent decisions (Human Provost function)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision_id": {"type": "string", "description": "Decision ID to approve/reject"},
                        "decision": {"type": "string", "enum": ["approve", "reject"], "description": "Decision"},
                        "reason": {"type": "string", "description": "Reason for decision"}
                    },
                    "required": ["decision_id", "decision"]
                }
            },
            {
                "name": "monitor_performance",
                "description": "Monitor GAD agent performance across university",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "university_id": {"type": "string", "description": "University ID"},
                        "gad_role": {"type": "string", "description": "Filter by GAD role"},
                        "timeframe": {"type": "string", "description": "Timeframe (24h, 7d, 30d)", "default": "24h"}
                    },
                    "required": ["university_id"]
                }
            }
        ]
        
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle University tool execution"""
        
        if name == "create_university":
            return await self._create_university(arguments)
        elif name == "get_university_status":
            return await self._get_university_status(arguments)
        elif name == "enroll_gad_agent":
            return await self._enroll_gad_agent(arguments)
        elif name == "create_gad_curriculum":
            return await self._create_gad_curriculum(arguments)
        elif name == "get_agent_progress":
            return await self._get_agent_progress(arguments)
        elif name == "approve_agent_decision":
            return await self._approve_agent_decision(arguments)
        elif name == "monitor_performance":
            return await self._monitor_performance(arguments)
        else:
            return {"status": "error", "message": f"Unknown tool: {name}"}
            
    async def _create_university(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new university for GAD training"""
        try:
            university_data = {
                "name": args["name"],
                "description": args["description"],
                "primary_specialization": args.get("specialization", "GAD Development"),
                "max_agents": args.get("max_agents", 100),
                "settings": {
                    "gad_focus": True,
                    "curriculum_template": "gad_standard",
                    "auto_enroll_agents": True,
                    "training_data_sharing": True
                },
                "isolation_level": "strict"
            }
            
            result = await self.dryad_request("POST", "/api/v1/university/", data=university_data)
            
            return {
                "status": "success",
                "university_id": result["id"],
                "university_name": result["name"],
                "message": f"University '{result['name']}' created successfully for GAD training"
            }
            
        except Exception as e:
            logger.error(f"Create university failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _get_university_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get university status and statistics"""
        try:
            university_id = args["university_id"]
            result = await self.dryad_request("GET", f"/api/v1/university/{university_id}")
            
            # Get additional statistics
            stats = await self.dryad_request(
                "GET", 
                f"/api/v1/university/{university_id}/statistics"
            )
            
            return {
                "status": "success",
                "university": result,
                "statistics": stats,
                "gad_summary": {
                    "total_gad_agents": stats.get("total_agents", 0),
                    "active_gad_agents": stats.get("active_agents", 0),
                    "completed_training": stats.get("graduated_agents", 0),
                    "average_performance": stats.get("average_agent_level", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Get university status failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _enroll_gad_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Enroll a GAD agent in university curriculum"""
        try:
            enrollment_data = {
                "university_id": args["university_id"],
                "agent_name": args["agent_name"],
                "gad_role": args["role"],
                "curriculum_id": args.get("curriculum_id", f"gad_{args['role']}_curriculum"),
                "training_mode": "intensive",
                "customization": {
                    "focus_areas": self._get_role_focus_areas(args["role"]),
                    "skill_requirements": self._get_role_requirements(args["role"])
                }
            }
            
            result = await self.dryad_request("POST", "/api/v1/university/enroll", data=enrollment_data)
            
            return {
                "status": "success",
                "enrollment_id": result["id"],
                "agent_name": args["agent_name"],
                "role": args["role"],
                "curriculum": result.get("curriculum", {}),
                "message": f"GAD agent '{args['agent_name']}' enrolled in {args['role']} curriculum"
            }
            
        except Exception as e:
            logger.error(f"Enroll GAD agent failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _create_gad_curriculum(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create GAD-specific curriculum"""
        try:
            curriculum_data = {
                "name": args["name"],
                "description": args["description"],
                "specialization": f"GAD {args['gad_role']}",
                "courses": args["courses"],
                "gad_integration": {
                    "target_role": args["gad_role"],
                    "lifecycle_focus": self._get_role_lifecycle_focus(args["gad_role"]),
                    "tool_requirements": self._get_role_tool_requirements(args["gad_role"]),
                    "assessment_criteria": self._get_role_assessment_criteria(args["gad_role"])
                }
            }
            
            result = await self.dryad_request("POST", "/api/v1/university/curriculum", data=curriculum_data)
            
            return {
                "status": "success",
                "curriculum_id": result["id"],
                "curriculum_name": result["name"],
                "target_role": args["gad_role"],
                "courses": result["courses"],
                "message": f"GAD curriculum '{result['name']}' created for {args['gad_role']} training"
            }
            
        except Exception as e:
            logger.error(f"Create GAD curriculum failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _get_agent_progress(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get GAD agent training progress"""
        try:
            agent_name = args["agent_name"]
            university_id = args.get("university_id", "default")
            
            # Get agent progress from university system
            result = await self.dryad_request(
                "GET", 
                f"/api/v1/university/agents/{agent_name}/progress",
                params={"university_id": university_id}
            )
            
            return {
                "status": "success",
                "agent_name": agent_name,
                "progress": result,
                "gad_readiness": {
                    "current_level": result.get("level", 0),
                    "completed_courses": result.get("completed_courses", []),
                    "skill_assessment": result.get("skills", {}),
                    "ready_for_role": result.get("level", 0) >= 3
                }
            }
            
        except Exception as e:
            logger.error(f"Get agent progress failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _approve_agent_decision(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Approve or reject GAD agent decision (Human Provost function)"""
        try:
            approval_data = {
                "decision_id": args["decision_id"],
                "decision": args["decision"],
                "reason": args.get("reason", ""),
                "approved_by": "human-provost",
                "timestamp": "now"
            }
            
            result = await self.dryad_request("POST", "/api/v1/university/approve", data=approval_data)
            
            return {
                "status": "success",
                "decision": args["decision"],
                "decision_id": args["decision_id"],
                "result": result,
                "message": f"Decision {args['decision_id']} {args['decision']}d by Human Provost"
            }
            
        except Exception as e:
            logger.error(f"Approve agent decision failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _monitor_performance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor GAD agent performance"""
        try:
            university_id = args["university_id"]
            params = {
                "gad_role": args.get("gad_role"),
                "timeframe": args.get("timeframe", "24h")
            }
            
            result = await self.dryad_request(
                "GET", 
                f"/api/v1/university/{university_id}/performance",
                params=params
            )
            
            return {
                "status": "success",
                "university_id": university_id,
                "timeframe": args.get("timeframe", "24h"),
                "performance": result,
                "gad_insights": {
                    "hierarchy_efficiency": result.get("coordination_score", 0),
                    "quality_gate_effectiveness": result.get("review_score", 0),
                    "execution_performance": result.get("execution_score", 0),
                    "overall_gad_score": result.get("gad_score", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Monitor performance failed: {e}")
            return {"status": "error", "message": str(e)}
            
    def _get_role_focus_areas(self, role: str) -> List[str]:
        """Get focus areas for GAD role"""
        focus_areas = {
            "forest-keeper": ["project_planning", "agent_coordination", "knowledge_management", "workflow_oversight"],
            "guardian-reviewer": ["quality_assurance", "security_analysis", "code_review", "compliance_checking"],
            "branch-weaver": ["code_execution", "tool_integration", "output_documentation", "collaboration"],
            "human-provost": ["strategic_oversight", "compliance_monitoring", "performance_management", "decision_authority"]
        }
        return focus_areas.get(role, ["general_skills"])
        
    def _get_role_requirements(self, role: str) -> List[str]:
        """Get skill requirements for GAD role"""
        requirements = {
            "forest-keeper": ["advanced_planning", "multi_agent_coordination", "knowledge_trees", "oracle_consultation"],
            "guardian-reviewer": ["security_review", "code_analysis", "tool_validation", "quality_gates"],
            "branch-weaver": ["code_generation", "tool_usage", "documentation", "multi_agent_communication"],
            "human-provost": ["strategic_thinking", "compliance_knowledge", "performance_analysis", "decision_making"]
        }
        return requirements.get(role, ["basic_skills"])
        
    def _get_role_lifecycle_focus(self, role: str) -> str:
        """Get lifecycle focus for GAD role"""
        focus = {
            "forest-keeper": "plan",
            "guardian-reviewer": "review", 
            "branch-weaver": "execute",
            "human-provost": "oversight"
        }
        return focus.get(role, "general")
        
    def _get_role_tool_requirements(self, role: str) -> List[str]:
        """Get tool requirements for GAD role"""
        tools = {
            "forest-keeper": ["gad_lifecycle_manager", "knowledge_tree_access", "agent_orchestration"],
            "guardian-reviewer": ["gad_quality_gate", "security_scanning", "tool_validation"],
            "branch-weaver": ["code_editor", "tool_registry_access", "gad_knowledge_persist"],
            "human-provost": ["university_admin", "performance_monitoring", "approval_workflow"]
        }
        return tools.get(role, ["basic_tools"])
        
    def _get_role_assessment_criteria(self, role: str) -> List[str]:
        """Get assessment criteria for GAD role"""
        criteria = {
            "forest-keeper": ["planning_accuracy", "coordination_effectiveness", "knowledge_management"],
            "guardian-reviewer": ["quality_detection", "security_compliance", "approval_accuracy"],
            "branch-weaver": ["code_quality", "execution_efficiency", "collaboration_quality"],
            "human-provost": ["decision_quality", "oversight_effectiveness", "strategic_alignment"]
        }
        return criteria.get(role, ["general_performance"])


# Main entry point for MCP server
if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = UniversityMCPServer()
        async with server:
            app = server.get_app()
            # Run the MCP server
            await app.run()
    
    asyncio.run(main())