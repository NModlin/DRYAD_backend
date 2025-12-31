"""
Domain Expert Agent Memory Integration

Integrates domain expert agents with the existing agent memory system:
- Shared memory storage for expert knowledge and sessions
- Context-aware memory retrieval for tutoring sessions
- Cross-expert knowledge sharing and learning
- Long-term memory persistence for continuous improvement
- Memory-based session recommendations and personalization
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
import asyncio
from collections import defaultdict

from app.university_system.database.models_university import (
    UniversityAgent, DomainExpertProfile, ExpertSession, KnowledgeNode,
    TeachingMethod, StudentLearningProfile
)
from app.university_system.services.agent_memory_service import AgentMemoryManager
from app.university_system.services.domain_expert_engine import DomainExpertEngine

logger = logging.getLogger(__name__)

class MemoryIntegrationType(str, Enum):
    """Types of memory integration between expert agents"""
    SESSION_MEMORY = "session_memory"
    KNOWLEDGE_MEMORY = "knowledge_memory"
    CONTEXT_MEMORY = "context_memory"
    LEARNING_MEMORY = "learning_memory"
    PREFERENCE_MEMORY = "preference_memory"

class MemoryImportance(str, Enum):
    """Importance levels for memory entries"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DomainExpertMemoryIntegration:
    """
    Integration system between domain expert agents and agent memory service:
    
    Features:
    - Shared memory storage for expert knowledge and sessions
    - Context-aware memory retrieval for enhanced tutoring
    - Cross-expert knowledge sharing and collaborative learning
    - Long-term memory persistence for continuous improvement
    - Personalized session recommendations based on memory
    """
    
    def __init__(self, db: Session, memory_service: AgentMemoryManager):
        self.db = db
        self.memory_service = memory_service
        self.expert_engine = DomainExpertEngine(db)
        
        # Memory integration patterns
        self.memory_patterns = {
            "session_knowledge": {
                "prefix": "session_knowledge",
                "memory_type": MemoryIntegrationType.SESSION_MEMORY,
                "retention_days": 365
            },
            "student_preferences": {
                "prefix": "student_prefs",
                "memory_type": MemoryIntegrationType.PREFERENCE_MEMORY,
                "retention_days": 730
            },
            "teaching_effectiveness": {
                "prefix": "teaching_effect",
                "memory_type": MemoryIntegrationType.LEARNING_MEMORY,
                "retention_days": 180
            },
            "knowledge_connections": {
                "prefix": "knowledge_conn",
                "memory_type": MemoryIntegrationType.KNOWLEDGE_MEMORY,
                "retention_days": -1  # Permanent
            },
            "context_patterns": {
                "prefix": "context_pat",
                "memory_type": MemoryIntegrationType.CONTEXT_MEMORY,
                "retention_days": 90
            }
        }
    
    async def store_expert_session_memory(
        self,
        session_id: str,
        expert_agent_id: str,
        student_id: str,
        session_data: Dict[str, Any],
        importance: MemoryImportance = MemoryImportance.MEDIUM
    ) -> Dict[str, Any]:
        """
        Store session memory for expert agent including tutoring context and outcomes.
        
        Args:
            session_id: ID of the expert session
            expert_agent_id: ID of the expert agent
            student_id: ID of the student
            session_data: Complete session data including interactions, outcomes, and context
            importance: Importance level of this memory entry
        
        Returns:
            Stored memory entry information
        """
        try:
            # Create session memory key
            memory_key = f"{self.memory_patterns['session_knowledge']['prefix']}:{expert_agent_id}:{session_id}"
            
            # Structure memory data
            memory_data = {
                "session_id": session_id,
                "expert_agent_id": expert_agent_id,
                "student_id": student_id,
                "domain": session_data.get("domain", ""),
                "topic": session_data.get("topic", ""),
                "difficulty_level": session_data.get("difficulty_level", "intermediate"),
                "session_outcomes": session_data.get("learning_objectives", []),
                "student_engagement_level": session_data.get("engagement_score", 0.5),
                "concepts_covered": session_data.get("concepts_explained", []),
                "assessment_results": session_data.get("assessment_results", {}),
                "next_steps_recommended": session_data.get("next_steps", []),
                "session_duration": session_data.get("duration_minutes", 0),
                "effectiveness_metrics": session_data.get("effectiveness_metrics", {}),
                "memory_timestamp": datetime.now(timezone.utc).isoformat(),
                "importance_level": importance,
                "retention_days": self.memory_patterns['session_knowledge']['retention_days']
            }
            
            # Store in agent memory service
            memory_result = await self.memory_service.store_agent_memory(
                agent_id=expert_agent_id,
                memory_key=memory_key,
                memory_data=memory_data,
                context_type="expert_session",
                importance=importance.value,
                retention_policy_days=self.memory_patterns['session_knowledge']['retention_days']
            )
            
            # Also store student-side memory for context retention
            student_memory_key = f"expert_session_context:{student_id}:{session_id}"
            student_memory_data = {
                "session_id": session_id,
                "expert_agent_id": expert_agent_id,
                "domain": session_data.get("domain", ""),
                "topic": session_data.get("topic", ""),
                "engagement_highlights": session_data.get("engagement_highlights", []),
                "learning_breakthroughs": session_data.get("breakthroughs", []),
                "remaining_challenges": session_data.get("challenges", []),
                "preferred_explanation_style": session_data.get("explanation_style", ""),
                "memory_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.memory_service.store_agent_memory(
                agent_id=student_id,
                memory_key=student_memory_key,
                memory_data=student_memory_data,
                context_type="student_session",
                importance=MemoryImportance.HIGH.value,
                retention_policy_days=730
            )
            
            logger.info(f"Stored expert session memory for session {session_id}")
            return {
                "memory_key": memory_key,
                "session_id": session_id,
                "expert_agent_id": expert_agent_id,
                "student_id": student_id,
                "stored_successfully": True,
                "memory_result": memory_result
            }
            
        except Exception as e:
            logger.error(f"Error storing expert session memory: {str(e)}")
            return {"error": str(e)}
    
    async def retrieve_relevant_session_context(
        self,
        expert_agent_id: str,
        student_id: str,
        current_topic: str,
        domain: str,
        context_window: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve relevant session context from memory to enhance current tutoring.
        
        Args:
            expert_agent_id: ID of the expert agent
            student_id: ID of the student
            current_topic: Topic being currently taught
            domain: Domain of expertise
            context_window: Number of previous sessions to consider
        
        Returns:
            Relevant session context and historical information
        """
        try:
            # Find similar sessions for the same student in the same domain
            session_pattern = f"session_knowledge:{expert_agent_id}:*"
            similar_sessions = await self.memory_service.retrieve_agent_memories(
                agent_id=student_id,
                pattern=session_pattern,
                limit=context_window
            )
            
            # Filter for relevant sessions
            relevant_sessions = []
            for session in similar_sessions:
                session_data = session.get("memory_data", {})
                if (session_data.get("domain") == domain and 
                    session_data.get("topic") and
                    session_data.get("topic").lower() in current_topic.lower()):
                    relevant_sessions.append(session)
            
            # Get student preferences from memory
            preference_pattern = f"student_prefs:{student_id}:*"
            student_preferences = await self.memory_service.retrieve_agent_memories(
                agent_id=student_id,
                pattern=preference_pattern,
                limit=5
            )
            
            # Analyze teaching effectiveness patterns
            effectiveness_pattern = f"teaching_effect:{expert_agent_id}:*"
            effectiveness_memories = await self.memory_service.retrieve_agent_memories(
                agent_id=expert_agent_id,
                pattern=effectiveness_pattern,
                limit=20
            )
            
            # Generate context summary
            context_summary = {
                "relevant_sessions": relevant_sessions,
                "student_preferences": student_preferences,
                "effectiveness_patterns": effectiveness_memories,
                "domain_context": {
                    "common_challenges": self._extract_common_challenges(relevant_sessions),
                    "successful_approaches": self._extract_successful_approaches(relevant_sessions),
                    "progression_milestones": self._extract_progression_milestones(relevant_sessions)
                },
                "personalization_insights": {
                    "preferred_explanation_style": self._determine_preferred_style(relevant_sessions),
                    "engagement_triggers": self._identify_engagement_triggers(relevant_sessions),
                    "optimal_difficulty_progression": self._analyze_difficulty_progression(relevant_sessions)
                }
            }
            
            return context_summary
            
        except Exception as e:
            logger.error(f"Error retrieving session context: {str(e)}")
            return {"error": str(e)}
    
    async def store_student_learning_preferences(
        self,
        student_id: str,
        domain: str,
        preferences: Dict[str, Any],
        session_outcomes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store and update student learning preferences based on session outcomes.
        
        Args:
            student_id: ID of the student
            domain: Domain of learning
            preferences: Learning preferences and style information
            session_outcomes: Outcomes from the learning session
        
        Returns:
            Updated preference storage result
        """
        try:
            # Create preference memory key
            preference_key = f"{self.memory_patterns['student_preferences']['prefix']}:{student_id}:{domain}"
            
            # Structure preference data
            preference_data = {
                "student_id": student_id,
                "domain": domain,
                "learning_style": preferences.get("learning_style", ""),
                "preferred_explanation_depth": preferences.get("explanation_depth", "moderate"),
                "engagement_preferences": preferences.get("engagement_preferences", {}),
                "difficulty_preference": preferences.get("difficulty_preference", "adaptive"),
                "communication_style": preferences.get("communication_style", ""),
                "session_outcomes": session_outcomes,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "confidence_level": preferences.get("confidence_level", 0.7),
                "memory_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in agent memory service
            memory_result = await self.memory_service.store_agent_memory(
                agent_id=student_id,
                memory_key=preference_key,
                memory_data=preference_data,
                context_type="learning_preferences",
                importance=MemoryImportance.HIGH.value,
                retention_policy_days=self.memory_patterns['student_preferences']['retention_days']
            )
            
            logger.info(f"Stored learning preferences for student {student_id} in domain {domain}")
            return {
                "preference_key": preference_key,
                "student_id": student_id,
                "domain": domain,
                "stored_successfully": True,
                "memory_result": memory_result
            }
            
        except Exception as e:
            logger.error(f"Error storing learning preferences: {str(e)}")
            return {"error": str(e)}
    
    async def share_knowledge_across_experts(
        self,
        knowledge_entry: Dict[str, Any],
        target_experts: List[str],
        sharing_context: str
    ) -> Dict[str, Any]:
        """
        Share knowledge and insights across multiple expert agents.
        
        Args:
            knowledge_entry: Knowledge to be shared
            target_experts: List of expert agent IDs to share with
            sharing_context: Context for why this knowledge is being shared
        
        Returns:
            Knowledge sharing results
        """
        try:
            sharing_results = []
            
            for expert_id in target_experts:
                # Create knowledge sharing memory
                sharing_key = f"{self.memory_patterns['knowledge_connections']['prefix']}:{expert_id}:{uuid.uuid4()}"
                
                # Structure sharing data
                sharing_data = {
                    "knowledge_source": knowledge_entry.get("source_expert_id", ""),
                    "knowledge_domain": knowledge_entry.get("domain", ""),
                    "knowledge_content": knowledge_entry.get("content", ""),
                    "knowledge_type": knowledge_entry.get("type", ""),
                    "effectiveness_score": knowledge_entry.get("effectiveness_score", 0.0),
                    "sharing_context": sharing_context,
                    "applicable_scenarios": knowledge_entry.get("applicable_scenarios", []),
                    "success_indicators": knowledge_entry.get("success_indicators", []),
                    "implementation_notes": knowledge_entry.get("implementation_notes", ""),
                    "cross_domain_applications": knowledge_entry.get("cross_domain_applications", []),
                    "memory_timestamp": datetime.now(timezone.utc).isoformat(),
                    "shared_by": "domain_expert_system"
                }
                
                # Store for target expert
                memory_result = await self.memory_service.store_agent_memory(
                    agent_id=expert_id,
                    memory_key=sharing_key,
                    memory_data=sharing_data,
                    context_type="shared_knowledge",
                    importance=MemoryImportance.MEDIUM.value,
                    retention_policy_days=self.memory_patterns['knowledge_connections']['retention_days']
                )
                
                sharing_results.append({
                    "expert_id": expert_id,
                    "sharing_key": sharing_key,
                    "memory_result": memory_result,
                    "shared_successfully": True
                })
            
            logger.info(f"Shared knowledge across {len(target_experts)} expert agents")
            return {
                "knowledge_sharing_id": str(uuid.uuid4()),
                "shared_with_experts": len(target_experts),
                "sharing_results": sharing_results,
                "sharing_context": sharing_context
            }
            
        except Exception as e:
            logger.error(f"Error sharing knowledge across experts: {str(e)}")
            return {"error": str(e)}
    
    async def recommend_next_learning_steps(
        self,
        student_id: str,
        current_expert_id: str,
        current_session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized learning step recommendations based on memory.
        
        Args:
            student_id: ID of the student
            current_expert_id: ID of the current expert agent
            current_session_data: Data from the current session
        
        Returns:
            Personalized learning step recommendations
        """
        try:
            # Retrieve student's learning history
            session_pattern = f"session_knowledge:*:{student_id}"
            learning_history = await self.memory_service.retrieve_agent_memories(
                agent_id=student_id,
                pattern=session_pattern,
                limit=20
            )
            
            # Retrieve student's preferences
            preference_pattern = f"student_prefs:{student_id}:*"
            student_prefs = await self.memory_service.retrieve_agent_memories(
                agent_id=student_id,
                pattern=preference_pattern,
                limit=5
            )
            
            # Analyze progress patterns
            progress_analysis = self._analyze_learning_progress(learning_history)
            
            # Generate recommendations
            recommendations = {
                "immediate_next_steps": self._generate_immediate_next_steps(
                    current_session_data, student_prefs
                ),
                "intermediate_goals": self._generate_intermediate_goals(
                    progress_analysis, current_session_data.get("domain", "")
                ),
                "long_term_pathway": self._generate_long_term_pathway(
                    progress_analysis, student_prefs
                ),
                "expert_recommendations": self._recommend_experts(
                    current_session_data.get("domain", ""), learning_history
                ),
                "resource_suggestions": self._suggest_resources(
                    current_session_data, student_prefs
                ),
                "assessment_opportunities": self._suggest_assessments(
                    progress_analysis, current_session_data
                )
            }
            
            # Store recommendations in memory for future reference
            recommendation_key = f"recommendations:{student_id}:{current_expert_id}:{uuid.uuid4()}"
            recommendation_data = {
                "student_id": student_id,
                "current_expert_id": current_expert_id,
                "recommendations": recommendations,
                "generation_context": current_session_data,
                "memory_timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence_score": self._calculate_recommendation_confidence(learning_history, student_prefs)
            }
            
            await self.memory_service.store_agent_memory(
                agent_id=current_expert_id,
                memory_key=recommendation_key,
                memory_data=recommendation_data,
                context_type="learning_recommendations",
                importance=MemoryImportance.HIGH.value,
                retention_policy_days=180
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating learning recommendations: {str(e)}")
            return {"error": str(e)}
    
    # ==================== Private Helper Methods ====================
    
    def _extract_common_challenges(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Extract common challenges from session history"""
        challenges = []
        for session in sessions:
            session_data = session.get("memory_data", {})
            remaining_challenges = session_data.get("remaining_challenges", [])
            challenges.extend(remaining_challenges)
        return list(set(challenges))  # Remove duplicates
    
    def _extract_successful_approaches(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Extract successful teaching approaches from session history"""
        approaches = []
        for session in sessions:
            session_data = session.get("memory_data", {})
            effectiveness_metrics = session_data.get("effectiveness_metrics", {})
            successful_approaches = effectiveness_metrics.get("successful_approaches", [])
            approaches.extend(successful_approaches)
        return list(set(approaches))
    
    def _extract_progression_milestones(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract learning progression milestones from session history"""
        milestones = []
        for session in sessions:
            session_data = session.get("memory_data", {})
            outcomes = session_data.get("session_outcomes", [])
            for outcome in outcomes:
                if outcome.get("achievement_level", "") == "milestone":
                    milestones.append({
                        "topic": outcome.get("topic", ""),
                        "achievement_date": outcome.get("timestamp", ""),
                        "difficulty_level": outcome.get("difficulty_level", "")
                    })
        return milestones
    
    def _determine_preferred_style(self, sessions: List[Dict[str, Any]]) -> str:
        """Determine student's preferred explanation style"""
        styles = []
        for session in sessions:
            session_data = session.get("memory_data", {})
            style = session_data.get("preferred_explanation_style", "")
            if style:
                styles.append(style)
        
        if not styles:
            return "adaptive"
        
        # Return most common style
        return max(set(styles), key=styles.count)
    
    def _identify_engagement_triggers(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Identify what engages this student most"""
        triggers = []
        for session in sessions:
            session_data = session.get("memory_data", {})
            engagement_highlights = session_data.get("engagement_highlights", [])
            triggers.extend(engagement_highlights)
        return list(set(triggers))
    
    def _analyze_difficulty_progression(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze student's difficulty progression pattern"""
        progressions = []
        for session in sessions:
            session_data = session.get("memory_data", {})
            difficulty = session_data.get("difficulty_level", "intermediate")
            engagement = session_data.get("student_engagement_level", 0.5)
            progressions.append({
                "difficulty": difficulty,
                "engagement": engagement
            })
        
        # Simple analysis - in real implementation, this would be more sophisticated
        return {
            "optimal_difficulty_range": self._find_optimal_difficulty(progressions),
            "progression_rate": self._calculate_progression_rate(progressions),
            "engagement_correlation": self._analyze_engagement_correlation(progressions)
        }
    
    def _find_optimal_difficulty(self, progressions: List[Dict[str, Any]]) -> str:
        """Find the difficulty level that produces highest engagement"""
        difficulty_scores = defaultdict(list)
        for prog in progressions:
            difficulty_scores[prog["difficulty"]].append(prog["engagement"])
        
        avg_scores = {k: sum(v) / len(v) for k, v in difficulty_scores.items()}
        return max(avg_scores, key=avg_scores.get) if avg_scores else "intermediate"
    
    def _calculate_progression_rate(self, progressions: List[Dict[str, Any]]) -> float:
        """Calculate how quickly student progresses through difficulty levels"""
        # Simplified calculation
        if len(progressions) < 2:
            return 0.0
        
        difficulty_order = ["beginner", "basic", "intermediate", "advanced", "expert"]
        scores = []
        
        for prog in progressions:
            try:
                score = difficulty_order.index(prog["difficulty"])
                scores.append(score)
            except ValueError:
                scores.append(2)  # Default to intermediate
        
        # Calculate rate of change
        if len(scores) > 1:
            changes = [scores[i] - scores[i-1] for i in range(1, len(scores))]
            return sum(changes) / len(changes) if changes else 0.0
        return 0.0
    
    def _analyze_engagement_correlation(self, progressions: List[Dict[str, Any]]) -> float:
        """Analyze correlation between difficulty and engagement"""
        if len(progressions) < 2:
            return 0.0
        
        difficulties = [p["difficulty"] for p in progressions]
        engagements = [p["engagement"] for p in progressions]
        
        # Simple correlation calculation
        # In real implementation, would use proper statistical correlation
        difficulty_range = len(set(difficulties))
        engagement_variance = max(engagements) - min(engagements)
        
        return 1.0 - (engagement_variance / difficulty_range) if difficulty_range > 0 else 0.5
    
    def _generate_immediate_next_steps(
        self, 
        session_data: Dict[str, Any], 
        preferences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate immediate next learning steps"""
        # Simplified implementation
        return [
            {
                "step": "Review key concepts covered in current session",
                "estimated_time": "10 minutes",
                "importance": "high"
            },
            {
                "step": "Practice with similar problems",
                "estimated_time": "20 minutes", 
                "importance": "high"
            },
            {
                "step": "Explore related topics for deeper understanding",
                "estimated_time": "15 minutes",
                "importance": "medium"
            }
        ]
    
    def _generate_intermediate_goals(
        self, 
        progress_analysis: Dict[str, Any], 
        domain: str
    ) -> List[Dict[str, Any]]:
        """Generate intermediate learning goals"""
        # Simplified implementation
        return [
            {
                "goal": f"Master core concepts in {domain}",
                "timeline": "2-3 sessions",
                "criteria": "Achieve 80% understanding"
            },
            {
                "goal": f"Apply {domain} knowledge to practical problems",
                "timeline": "1-2 sessions",
                "criteria": "Solve 3 problems independently"
            }
        ]
    
    def _generate_long_term_pathway(
        self, 
        progress_analysis: Dict[str, Any], 
        preferences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate long-term learning pathway"""
        # Simplified implementation
        return [
            {
                "phase": "Foundation Building",
                "duration": "2-4 weeks",
                "objectives": ["Master basics", "Build confidence"]
            },
            {
                "phase": "Skill Development",
                "duration": "4-6 weeks", 
                "objectives": ["Apply skills", "Handle complexity"]
            },
            {
                "phase": "Expert Mastery",
                "duration": "6-8 weeks",
                "objectives": ["Advanced applications", "Teach others"]
            }
        ]
    
    def _recommend_experts(
        self, 
        domain: str, 
        learning_history: List[Dict[str, Any]]
    ) -> List[str]:
        """Recommend other experts for continued learning"""
        # Simplified implementation - would query expert database
        recommendations = {
            "mathematics": ["Dr. Algebra Specialist", "Dr. Calculus Expert"],
            "science": ["Dr. Physics Master", "Dr. Chemistry Pro"],
            "language": ["Dr. Grammar Expert", "Dr. Literature Scholar"],
            "history": ["Dr. Ancient History", "Dr. Modern History"],
            "computer_science": ["Dr. Algorithms Expert", "Dr. Programming Guru"]
        }
        return recommendations.get(domain, ["Dr. General Expert"])
    
    def _suggest_resources(
        self, 
        session_data: Dict[str, Any], 
        preferences: List[Dict[str, Any]]
    ) -> List[str]:
        """Suggest learning resources based on memory and preferences"""
        # Simplified implementation
        return [
            "Interactive online exercises",
            "Video tutorials for visual learners",
            "Practice problem sets",
            "Peer discussion forums"
        ]
    
    def _suggest_assessments(
        self, 
        progress_analysis: Dict[str, Any], 
        session_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest appropriate assessment opportunities"""
        # Simplified implementation
        return [
            {
                "type": "Quick comprehension check",
                "timing": "End of current session",
                "format": "Multiple choice"
            },
            {
                "type": "Skill application test",
                "timing": "After 2-3 sessions",
                "format": "Problem solving"
            },
            {
                "type": "Comprehensive assessment",
                "timing": "After topic completion",
                "format": "Project-based"
            }
        ]
    
    def _calculate_recommendation_confidence(
        self, 
        learning_history: List[Dict[str, Any]], 
        preferences: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for recommendations"""
        # Base confidence on amount of historical data
        history_score = min(len(learning_history) / 10.0, 1.0)  # Max confidence at 10+ sessions
        preference_score = min(len(preferences) / 3.0, 1.0)    # Max confidence at 3+ preference records
        
        # Weighted average
        confidence = (history_score * 0.7) + (preference_score * 0.3)
        return min(confidence, 0.95)  # Cap at 95% confidence
    
    def _analyze_learning_progress(self, learning_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze student's learning progress from session history"""
        # Simplified progress analysis
        if not learning_history:
            return {"progress_level": "beginning", "strengths": [], "areas_for_improvement": []}
        
        total_sessions = len(learning_history)
        avg_engagement = sum(
            session.get("memory_data", {}).get("student_engagement_level", 0.5)
            for session in learning_history
        ) / total_sessions
        
        # Determine progress level
        if avg_engagement > 0.8:
            progress_level = "advanced"
        elif avg_engagement > 0.6:
            progress_level = "intermediate"
        elif avg_engagement > 0.4:
            progress_level = "developing"
        else:
            progress_level = "beginning"
        
        return {
            "total_sessions": total_sessions,
            "average_engagement": avg_engagement,
            "progress_level": progress_level,
            "engagement_trend": "stable",  # Simplified
            "consistency_score": min(avg_engagement * 1.2, 1.0)
        }