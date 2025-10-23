"""
Agent Architect Service

Service for assisting users in creating high-quality Agent Sheets.
Converts natural language descriptions into validated JSON specifications.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.custom_agent import AgentSheet
from app.services.agent_factory import AgentValidator

logger = logging.getLogger(__name__)


class AgentArchitectService:
    """Service for interactive agent design assistance."""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = AgentValidator(db)
        self.conversation_state = {}
    
    async def start_conversation(
        self,
        user_id: str,
        initial_request: str
    ) -> Dict[str, Any]:
        """
        Start a new agent design conversation.
        
        Args:
            user_id: ID of the user requesting assistance
            initial_request: Natural language description of desired agent
            
        Returns:
            Dict with conversation_id and first question
        """
        try:
            conversation_id = f"{user_id}_{datetime.utcnow().timestamp()}"
            
            # Initialize conversation state
            self.conversation_state[conversation_id] = {
                "user_id": user_id,
                "initial_request": initial_request,
                "gathered_info": {},
                "current_step": "role",
                "agent_sheet": {}
            }
            
            # Analyze initial request
            analysis = self._analyze_request(initial_request)
            
            # Determine first question
            first_question = self._get_next_question(conversation_id, analysis)
            
            logger.info(f"✅ Started agent design conversation: {conversation_id}")
            
            return {
                "conversation_id": conversation_id,
                "message": first_question,
                "progress": self._get_progress(conversation_id),
                "analysis": analysis
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to start conversation: {e}")
            raise
    
    async def continue_conversation(
        self,
        conversation_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Continue an existing agent design conversation.
        
        Args:
            conversation_id: ID of the conversation
            user_response: User's response to the previous question
            
        Returns:
            Dict with next question or completed agent sheet
        """
        try:
            if conversation_id not in self.conversation_state:
                raise ValueError(f"Conversation '{conversation_id}' not found")
            
            state = self.conversation_state[conversation_id]
            current_step = state["current_step"]
            
            # Process user response
            self._process_response(conversation_id, current_step, user_response)
            
            # Check if we have all required information
            if self._is_complete(conversation_id):
                # Generate agent sheet
                agent_sheet = self._generate_agent_sheet(conversation_id)
                
                # Validate agent sheet
                validation_result = self.validator.validate_agent_sheet(agent_sheet)
                
                logger.info(f"✅ Completed agent design: {conversation_id}")
                
                return {
                    "conversation_id": conversation_id,
                    "status": "complete",
                    "agent_sheet": agent_sheet,
                    "validation": {
                        "valid": validation_result.valid,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings
                    },
                    "message": "Agent sheet created successfully! Review and submit when ready."
                }
            
            # Get next question
            next_question = self._get_next_question(conversation_id)
            
            return {
                "conversation_id": conversation_id,
                "status": "in_progress",
                "message": next_question,
                "progress": self._get_progress(conversation_id)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to continue conversation: {e}")
            raise
    
    def _analyze_request(self, request: str) -> Dict[str, Any]:
        """
        Analyze the initial request to extract information.
        
        Simple keyword-based analysis. In production, this would use NLP/LLM.
        """
        request_lower = request.lower()
        
        analysis = {
            "detected_role": None,
            "detected_category": None,
            "detected_capabilities": [],
            "complexity": "medium"
        }
        
        # Detect role keywords
        role_keywords = {
            "customer support": "customer_support",
            "code review": "code_reviewer",
            "testing": "test_engineer",
            "documentation": "documentation_writer",
            "analysis": "analyst",
            "research": "researcher"
        }
        
        for keyword, role in role_keywords.items():
            if keyword in request_lower:
                analysis["detected_role"] = role
                break
        
        # Detect category
        category_keywords = {
            "development": ["code", "programming", "development"],
            "qa": ["test", "quality", "qa"],
            "support": ["support", "help", "customer"],
            "analysis": ["analyze", "analysis", "data"],
            "documentation": ["document", "documentation", "writing"]
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in request_lower for kw in keywords):
                analysis["detected_category"] = category
                break
        
        # Detect capabilities
        capability_keywords = {
            "code_review": ["review", "code review"],
            "testing": ["test", "testing"],
            "documentation": ["document", "documentation"],
            "analysis": ["analyze", "analysis"],
            "search": ["search", "find"],
            "communication": ["communicate", "respond", "answer"]
        }
        
        for capability, keywords in capability_keywords.items():
            if any(kw in request_lower for kw in keywords):
                analysis["detected_capabilities"].append(capability)
        
        return analysis
    
    def _get_next_question(
        self,
        conversation_id: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get the next question to ask the user."""
        state = self.conversation_state[conversation_id]
        gathered = state["gathered_info"]
        
        # Question flow
        if "role" not in gathered:
            if analysis and analysis.get("detected_role"):
                return f"I detected you want a '{analysis['detected_role']}' agent. Is that correct? If not, please describe the role."
            return "What role should this agent perform? (e.g., 'customer support specialist', 'code reviewer')"
        
        if "goal" not in gathered:
            return "What is the primary goal of this agent? What should it accomplish?"
        
        if "category" not in gathered:
            if analysis and analysis.get("detected_category"):
                return f"I think this agent fits in the '{analysis['detected_category']}' category. Is that correct?"
            return "What category does this agent belong to? (development, qa, support, analysis, documentation, operations)"
        
        if "capabilities" not in gathered:
            suggested = analysis.get("detected_capabilities", []) if analysis else []
            if suggested:
                return f"I detected these capabilities: {', '.join(suggested)}. Are these correct? Add or remove as needed."
            return "What capabilities should this agent have? (comma-separated list)"
        
        if "tone" not in gathered:
            return "What tone should the agent use? (professional, friendly, technical, casual)"
        
        if "constraints" not in gathered:
            return "Are there any constraints or limitations? (e.g., 'never delete data', 'always ask before executing'). Say 'none' if not applicable."
        
        if "tools" not in gathered:
            return "What tools should this agent have access to? (e.g., 'database_query', 'web_search'). Say 'none' for no tools."
        
        return "All information gathered!"
    
    def _process_response(
        self,
        conversation_id: str,
        step: str,
        response: str
    ) -> None:
        """Process user response and update conversation state."""
        state = self.conversation_state[conversation_id]
        gathered = state["gathered_info"]
        
        if step == "role":
            gathered["role"] = response.strip()
            state["current_step"] = "goal"
        
        elif step == "goal":
            gathered["goal"] = response.strip()
            state["current_step"] = "category"
        
        elif step == "category":
            gathered["category"] = response.strip().lower()
            state["current_step"] = "capabilities"
        
        elif step == "capabilities":
            if response.lower() != "none":
                capabilities = [c.strip() for c in response.split(",")]
                gathered["capabilities"] = capabilities
            else:
                gathered["capabilities"] = []
            state["current_step"] = "tone"
        
        elif step == "tone":
            gathered["tone"] = response.strip().lower()
            state["current_step"] = "constraints"
        
        elif step == "constraints":
            if response.lower() != "none":
                constraints = [c.strip() for c in response.split(",")]
                gathered["constraints"] = constraints
            else:
                gathered["constraints"] = []
            state["current_step"] = "tools"
        
        elif step == "tools":
            if response.lower() != "none":
                tools = [t.strip() for t in response.split(",")]
                gathered["tools"] = tools
            else:
                gathered["tools"] = []
            state["current_step"] = "complete"
    
    def _is_complete(self, conversation_id: str) -> bool:
        """Check if all required information has been gathered."""
        state = self.conversation_state[conversation_id]
        gathered = state["gathered_info"]
        
        required_fields = ["role", "goal", "category", "capabilities", "tone"]
        return all(field in gathered for field in required_fields)
    
    def _generate_agent_sheet(self, conversation_id: str) -> Dict[str, Any]:
        """Generate a complete agent sheet from gathered information."""
        state = self.conversation_state[conversation_id]
        gathered = state["gathered_info"]
        
        # Generate agent name from role
        agent_name = gathered["role"].lower().replace(" ", "_")
        
        agent_sheet = {
            "name": agent_name,
            "display_name": gathered["role"].title(),
            "role": gathered["role"],
            "goal": gathered["goal"],
            "backstory": f"You are a {gathered['role']} focused on {gathered['goal']}.",
            "category": gathered["category"],
            "capabilities": gathered["capabilities"],
            "tone": gathered["tone"],
            "constraints": gathered.get("constraints", []),
            "tools": gathered.get("tools", []),
            "llm_config": {
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "version": "1.0.0"
        }
        
        return agent_sheet
    
    def _get_progress(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation progress."""
        state = self.conversation_state[conversation_id]
        gathered = state["gathered_info"]
        
        total_steps = 7  # role, goal, category, capabilities, tone, constraints, tools
        completed_steps = len(gathered)
        
        return {
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "percentage": int((completed_steps / total_steps) * 100),
            "gathered_info": list(gathered.keys())
        }

