"""
Agent Memory Service

Provides comprehensive agent memory capabilities including:
- Conversation context persistence for cross-session memory
- Learning context management for problem-solving and decision making
- Knowledge entity storage for semantic understanding
- MCP server integration for sequential thinking and knowledge graph
- Context-aware intelligence for improved agent performance
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import asyncio
import asyncio.subprocess as subprocess

from dryad.university.database.models_university import (
    UniversityAgent,
    ConversationSession,
    LearningContext,
    KnowledgeEntity
)

logger = logging.getLogger(__name__)


class AgentMemoryManager:
    """Manages agent memory operations and MCP integration"""
    
    def __init__(self, db: Session):
        """Initialize memory manager with database session"""
        self.db = db
        self._mcp_clients = {}
    
    # ==================== Conversation Session Management ====================
    
    def save_conversation_context(
        self,
        agent_id: str,
        session_type: str = "interaction",
        context_data: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationSession:
        """Save conversational context for persistent memory"""
        
        if context_data is None:
            context_data = {}
        if conversation_history is None:
            conversation_history = []
        
        session = ConversationSession(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            session_type=session_type,
            context_data=context_data,
            conversation_history=conversation_history,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created conversation session {session.id} for agent {agent_id}")
        return session
    
    def update_conversation_session(
        self,
        session_id: str,
        context_data: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[ConversationSession]:
        """Update an existing conversation session"""
        
        session = self.db.query(ConversationSession).filter(
            ConversationSession.id == session_id
        ).first()
        
        if not session:
            return None
        
        if context_data is not None:
            session.context_data = context_data
        if conversation_history is not None:
            session.conversation_history = conversation_history
        
        session.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_conversation_sessions(
        self,
        agent_id: str,
        session_type: Optional[str] = None,
        limit: int = 10,
        skip: int = 0
    ) -> List[ConversationSession]:
        """Get conversation sessions for an agent"""
        
        query = self.db.query(ConversationSession).filter(
            ConversationSession.agent_id == agent_id
        )
        
        if session_type:
            query = query.filter(ConversationSession.session_type == session_type)
        
        return query.order_by(
            ConversationSession.updated_at.desc()
        ).offset(skip).limit(limit).all()
    
    # ==================== Learning Context Management ====================
    
    def create_learning_context(
        self,
        agent_id: str,
        context_type: str,
        context_data: Dict[str, Any],
        success_patterns: Optional[List[str]] = None,
        failure_patterns: Optional[List[str]] = None,
        applicable_scenarios: Optional[List[str]] = None,
        confidence_score: float = 0.0
    ) -> LearningContext:
        """Create a new learning context for an agent"""
        
        if success_patterns is None:
            success_patterns = []
        if failure_patterns is None:
            failure_patterns = []
        if applicable_scenarios is None:
            applicable_scenarios = []
        
        learning_context = LearningContext(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            context_type=context_type,
            context_data=context_data,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            applicable_scenarios=applicable_scenarios,
            confidence_score=confidence_score,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(learning_context)
        self.db.commit()
        self.db.refresh(learning_context)
        
        logger.info(f"Created learning context {learning_context.id} for agent {agent_id}")
        return learning_context
    
    def get_relevant_context(
        self,
        agent_id: str,
        query_context: str,
        context_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 5
    ) -> List[LearningContext]:
        """Retrieve relevant learning context for current situation"""
        
        query = self.db.query(LearningContext).filter(
            LearningContext.agent_id == agent_id
        ).filter(LearningContext.confidence_score >= min_confidence)
        
        if context_types:
            query = query.filter(LearningContext.context_type.in_(context_types))
        
        # Use a simple text matching approach for demonstration
        # In production, this would use semantic similarity or embeddings
        contexts = query.order_by(
            LearningContext.confidence_score.desc(),
            LearningContext.updated_at.desc()
        ).limit(limit * 3).all()  # Get more to filter
        
        # Simple relevance filtering (in production, use embeddings)
        relevant_contexts = []
        query_words = set(query_context.lower().split())
        
        for context in contexts:
            # Check context data and scenarios for relevance
            context_text = json.dumps(context.context_data).lower()
            scenario_text = " ".join(context.applicable_scenarios).lower()
            context_words = set(context_text.split() + scenario_text.split())
            
            # Calculate simple overlap score
            overlap = len(query_words.intersection(context_words))
            if overlap > 0:
                relevant_contexts.append(context)
                if len(relevant_contexts) >= limit:
                    break
        
        return relevant_contexts
    
    def update_learning(
        self,
        agent_id: str,
        outcome: Dict[str, Any],
        context: Dict[str, Any],
        success: bool,
        additional_context: Optional[str] = None
    ) -> LearningContext:
        """Update learning based on outcome of actions"""
        
        # Create or update learning context based on outcome
        context_type = context.get("type", "decision_making")
        learning_data = {
            "outcome": outcome,
            "context": context,
            "additional_context": additional_context
        }
        
        if success:
            # Update existing high-confidence contexts or create new ones
            existing_contexts = self.db.query(LearningContext).filter(
                and_(
                    LearningContext.agent_id == agent_id,
                    LearningContext.context_type == context_type,
                    LearningContext.confidence_score >= 0.7
                )
            ).all()
            
            if existing_contexts:
                # Update the most relevant existing context
                context_to_update = existing_contexts[0]
                if "success_patterns" not in context_to_update.context_data:
                    context_to_update.context_data["success_patterns"] = []
                
                context_to_update.context_data["success_patterns"].append(learning_data)
                context_to_update.confidence_score = min(1.0, context_to_update.confidence_score + 0.1)
                context_to_update.updated_at = datetime.now(timezone.utc)
                
                self.db.commit()
                self.db.refresh(context_to_update)
                return context_to_update
        
        # Create new learning context
        return self.create_learning_context(
            agent_id=agent_id,
            context_type=context_type,
            context_data=learning_data,
            success_patterns=[learning_data] if success else [],
            failure_patterns=[learning_data] if not success else [],
            applicable_scenarios=[additional_context] if additional_context else [],
            confidence_score=0.5 if success else 0.3
        )
    
    # ==================== Knowledge Entity Management ====================
    
    def create_knowledge_entity(
        self,
        agent_id: str,
        entity_type: str,
        entity_name: str,
        entity_data: Dict[str, Any],
        connections: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.0,
        source_context: Optional[str] = None
    ) -> KnowledgeEntity:
        """Create a new knowledge entity for an agent"""
        
        if connections is None:
            connections = []
        
        knowledge_entity = KnowledgeEntity(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            entity_type=entity_type,
            entity_name=entity_name,
            entity_data=entity_data,
            connections=connections,
            confidence=confidence,
            source_context=source_context,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(knowledge_entity)
        self.db.commit()
        self.db.refresh(knowledge_entity)
        
        logger.info(f"Created knowledge entity {knowledge_entity.id} for agent {agent_id}")
        return knowledge_entity
    
    def get_agent_knowledge_entities(
        self,
        agent_id: str,
        entity_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[KnowledgeEntity]:
        """Get knowledge entities for an agent"""
        
        query = self.db.query(KnowledgeEntity).filter(
            KnowledgeEntity.agent_id == agent_id
        ).filter(KnowledgeEntity.confidence >= min_confidence)
        
        if entity_type:
            query = query.filter(KnowledgeEntity.entity_type == entity_type)
        
        return query.order_by(
            KnowledgeEntity.confidence.desc(),
            KnowledgeEntity.updated_at.desc()
        ).limit(limit).all()
    
    def build_knowledge_graph(self, agent_id: str) -> Dict[str, Any]:
        """Build semantic knowledge representation for agent"""
        
        entities = self.get_agent_knowledge_entities(agent_id, min_confidence=0.5)
        
        graph = {
            "agent_id": agent_id,
            "total_entities": len(entities),
            "entity_types": {},
            "connections": [],
            "high_confidence_entities": [],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze entity types and build connection graph
        for entity in entities:
            # Track entity types
            if entity.entity_type not in graph["entity_types"]:
                graph["entity_types"][entity.entity_type] = 0
            graph["entity_types"][entity.entity_type] += 1
            
            # Track high confidence entities
            if entity.confidence >= 0.8:
                graph["high_confidence_entities"].append({
                    "id": entity.id,
                    "name": entity.entity_name,
                    "type": entity.entity_type,
                    "confidence": entity.confidence,
                    "connections_count": len(entity.connections)
                })
            
            # Process connections
            for connection in entity.connections:
                graph["connections"].append({
                    "source": entity.id,
                    "source_name": entity.entity_name,
                    "target": connection.get("target"),
                    "relationship": connection.get("relationship", "related_to"),
                    "strength": connection.get("strength", 0.5)
                })
        
        return graph
    
    # ==================== MCP Integration Methods ====================
    
    async def initialize_mcp_clients(self):
        """Initialize MCP clients for sequential thinking and knowledge graph"""
        try:
            # Initialize Sequential Thinking MCP
            self._mcp_clients["sequential_thinking"] = await self._connect_sequential_thinking()
            
            # Initialize Knowledge Graph MCP
            self._mcp_clients["knowledge_graph"] = await self._connect_knowledge_graph()
            
            logger.info("MCP clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {e}")
            raise
    
    async def _connect_sequential_thinking(self) -> Optional[Any]:
        """Connect to Sequential Thinking MCP server"""
        try:
            # This would connect to the actual MCP server
            # For now, we'll create a mock implementation
            client = {
                "type": "sequential_thinking",
                "connected": True,
                "last_heartbeat": datetime.now(timezone.utc)
            }
            return client
        except Exception as e:
            logger.warning(f"Sequential Thinking MCP not available: {e}")
            return None
    
    async def _connect_knowledge_graph(self) -> Optional[Any]:
        """Connect to Knowledge Graph MCP server"""
        try:
            # This would connect to the actual MCP server
            # For now, we'll create a mock implementation
            client = {
                "type": "knowledge_graph",
                "connected": True,
                "last_heartbeat": datetime.now(timezone.utc)
            }
            return client
        except Exception as e:
            logger.warning(f"Knowledge Graph MCP not available: {e}")
            return None
    
    async def sequential_thinking_process(
        self,
        problem: str,
        agent_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use sequential thinking MCP for complex problem-solving"""
        
        if "sequential_thinking" not in self._mcp_clients:
            await self.initialize_mcp_clients()
        
        client = self._mcp_clients.get("sequential_thinking")
        if not client or not client.get("connected"):
            # Fallback to local sequential thinking
            return await self._local_sequential_thinking(problem, context)
        
        try:
            # In production, this would call the actual MCP server
            thought_process = await self._call_mcp_sequential_thinking(problem, context)
            
            # Store the thinking process as learning context
            learning_context = self.create_learning_context(
                agent_id=agent_id,
                context_type="problem_solving",
                context_data={
                    "problem": problem,
                    "thought_process": thought_process,
                    "approach": "sequential_thinking_mcp"
                },
                success_patterns=[thought_process.get("insights", [])],
                applicable_scenarios=[problem],
                confidence_score=0.8
            )
            
            return {
                "success": True,
                "thoughts": thought_process.get("thoughts", []),
                "solution": thought_process.get("solution", ""),
                "confidence": thought_process.get("confidence", 0.7),
                "learning_context_id": learning_context.id
            }
            
        except Exception as e:
            logger.error(f"Sequential thinking MCP error: {e}")
            return await self._local_sequential_thinking(problem, context)
    
    async def _local_sequential_thinking(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Local fallback for sequential thinking"""
        
        thoughts = [
            f"Analyzing problem: {problem}",
            "Breaking down the problem into components",
            "Considering multiple approaches",
            "Evaluating potential solutions",
            "Selecting the best approach"
        ]
        
        return {
            "thoughts": thoughts,
            "solution": f"Solution approach for: {problem}",
            "confidence": 0.6,
            "method": "local_sequential_thinking"
        }
    
    async def _call_mcp_sequential_thinking(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call actual MCP sequential thinking server"""
        # This would be implemented to call the real MCP server
        # For now, return a mock response
        await asyncio.sleep(0.1)  # Simulate network call
        return await self._local_sequential_thinking(problem, context)
    
    async def knowledge_graph_analysis(
        self,
        agent_id: str,
        query: str,
        analysis_type: str = "semantic_search"
    ) -> Dict[str, Any]:
        """Use knowledge graph MCP for semantic understanding"""
        
        if "knowledge_graph" not in self._mcp_clients:
            await self.initialize_mcp_clients()
        
        client = self._mcp_clients.get("knowledge_graph")
        if not client or not client.get("connected"):
            # Fallback to local knowledge graph analysis
            return await self._local_knowledge_graph_analysis(agent_id, query)
        
        try:
            # Get agent's knowledge entities
            entities = self.get_agent_knowledge_entities(agent_id)
            
            # In production, this would call the actual MCP server
            analysis_result = await self._call_mcp_knowledge_graph(entities, query, analysis_type)
            
            # Create knowledge entity for the analysis
            knowledge_entity = self.create_knowledge_entity(
                agent_id=agent_id,
                entity_type="analysis_result",
                entity_name=f"Analysis: {query}",
                entity_data={
                    "query": query,
                    "analysis_type": analysis_type,
                    "results": analysis_result,
                    "source": "mcp_knowledge_graph"
                },
                confidence=0.8,
                source_context=f"knowledge_graph_analysis_{analysis_type}"
            )
            
            return {
                "success": True,
                "analysis": analysis_result,
                "entities_found": len(analysis_result.get("entities", [])),
                "connections": analysis_result.get("connections", []),
                "confidence": analysis_result.get("confidence", 0.7),
                "knowledge_entity_id": knowledge_entity.id
            }
            
        except Exception as e:
            logger.error(f"Knowledge graph MCP error: {e}")
            return await self._local_knowledge_graph_analysis(agent_id, query)
    
    async def _local_knowledge_graph_analysis(
        self,
        agent_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Local fallback for knowledge graph analysis"""
        
        entities = self.get_agent_knowledge_entities(agent_id)
        
        # Simple text matching for demonstration
        query_words = set(query.lower().split())
        relevant_entities = []
        connections = []
        
        for entity in entities:
            entity_text = f"{entity.entity_name} {json.dumps(entity.entity_data)}".lower()
            entity_words = set(entity_text.split())
            
            if query_words.intersection(entity_words):
                relevant_entities.append({
                    "id": entity.id,
                    "name": entity.entity_name,
                    "type": entity.entity_type,
                    "confidence": entity.confidence
                })
                
                # Add connections
                for connection in entity.connections:
                    connections.append({
                        "source": entity.entity_name,
                        "relationship": connection.get("relationship", "related_to"),
                        "target": connection.get("target", "unknown")
                    })
        
        return {
            "entities": relevant_entities,
            "connections": connections,
            "confidence": 0.6,
            "method": "local_knowledge_graph_analysis",
            "total_entities_analyzed": len(entities)
        }
    
    async def _call_mcp_knowledge_graph(
        self,
        entities: List[KnowledgeEntity],
        query: str,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Call actual MCP knowledge graph server"""
        # This would be implemented to call the real MCP server
        # For now, return a mock response
        await asyncio.sleep(0.1)  # Simulate network call
        return {
            "entities": [{"id": "mock", "name": "Mock Entity", "confidence": 0.8}],
            "connections": [],
            "confidence": 0.7,
            "method": "mcp_knowledge_graph"
        }
    
    def get_memory_analytics(self, agent_id: str) -> Dict[str, Any]:
        """Get analytics about agent memory usage"""
        
        # Conversation session stats
        session_count = self.db.query(func.count(ConversationSession.id)).filter(
            ConversationSession.agent_id == agent_id
        ).scalar() or 0
        
        # Learning context stats
        learning_count = self.db.query(func.count(LearningContext.id)).filter(
            LearningContext.agent_id == agent_id
        ).scalar() or 0
        
        high_confidence_learning = self.db.query(func.count(LearningContext.id)).filter(
            and_(
                LearningContext.agent_id == agent_id,
                LearningContext.confidence_score >= 0.7
            )
        ).scalar() or 0
        
        # Knowledge entity stats
        entity_count = self.db.query(func.count(KnowledgeEntity.id)).filter(
            KnowledgeEntity.agent_id == agent_id
        ).scalar() or 0
        
        high_confidence_entities = self.db.query(func.count(KnowledgeEntity.id)).filter(
            and_(
                KnowledgeEntity.agent_id == agent_id,
                KnowledgeEntity.confidence >= 0.8
            )
        ).scalar() or 0
        
        # MCP client status
        mcp_status = {
            "sequential_thinking": self._mcp_clients.get("sequential_thinking", {}).get("connected", False),
            "knowledge_graph": self._mcp_clients.get("knowledge_graph", {}).get("connected", False)
        }
        
        return {
            "agent_id": agent_id,
            "conversation_sessions": {
                "total": session_count,
                "recent_sessions": len(self.get_conversation_sessions(agent_id, limit=5))
            },
            "learning_contexts": {
                "total": learning_count,
                "high_confidence": high_confidence_learning,
                "average_confidence": self.db.query(func.avg(LearningContext.confidence_score)).filter(
                    LearningContext.agent_id == agent_id
                ).scalar() or 0.0
            },
            "knowledge_entities": {
                "total": entity_count,
                "high_confidence": high_confidence_entities,
                "average_confidence": self.db.query(func.avg(KnowledgeEntity.confidence)).filter(
                    KnowledgeEntity.agent_id == agent_id
                ).scalar() or 0.0
            },
            "mcp_status": mcp_status,
            "analytics_generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def get_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """Aggregate all memory types for an agent"""
        conversations = self.get_conversation_sessions(agent_id, limit=20)
        learning = self.get_relevant_context(agent_id, query_context="general", limit=20)
        knowledge = self.get_agent_knowledge_entities(agent_id, limit=50)
        
        return {
            "conversations": [c.__dict__ for c in conversations],
            "learning_contexts": [l.__dict__ for l in learning],
            "knowledge_entities": [k.__dict__ for k in knowledge],
            "retrieved_at": datetime.now(timezone.utc)
        }
    
    async def store_learning_insight(self, agent_id: str, insight_name: str, insight_data: Dict[str, Any]):
        """Store a learning insight"""
        return self.create_learning_context(
            agent_id=agent_id,
            context_type=insight_data.get("type", "insight"),
            context_data=insight_data.get("data", {}),
            success_patterns=[],
            confidence_score=0.9
        )