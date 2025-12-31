"""
Domain Expert Engine

Manages domain expert agents and their tutoring capabilities:
- Assigning appropriate expert tutors to students
- Creating personalized teaching plans
- Adapting difficulty based on student performance
- Generating explanations in preferred teaching styles
- Creating practice problems and assessments
- Tracking teaching effectiveness and learning outcomes
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
import logging
from datetime import datetime, timezone

from app.university_system.database.models_university import (
    UniversityAgent, DomainExpertProfile, ExpertSession, KnowledgeNode,
    TeachingMethod, StudentLearningProfile, AdaptiveLearningPath,
    University
)
from app.university_system.services.agent_memory_service import AgentMemoryManager

logger = logging.getLogger(__name__)

class DomainExpertEngine:
    """
    Core engine for managing domain expert agents and their tutoring capabilities.
    
    This engine provides:
    - Intelligent assignment of expert tutors to students
    - Adaptive difficulty adjustment based on performance
    - Personalized teaching plan generation
    - Multi-modal explanation generation
    - Comprehensive learning analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.memory_service = AgentMemoryManager(db)
        
    async def assign_expert_tutor(
        self, 
        student_id: str, 
        domain: str, 
        topic: str,
        specific_requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[UniversityAgent]:
        """
        Assign the most appropriate expert agent for a student based on:
        - Domain expertise level
        - Student learning profile
        - Teaching effectiveness history
        - Current availability and performance
        """
        try:
            # Get student's learning profile
            learning_profile = self.db.query(StudentLearningProfile).filter(
                and_(
                    StudentLearningProfile.agent_id == student_id,
                    StudentLearningProfile.domain == domain
                )
            ).first()
            
            # Get available expert agents in the domain
            expert_profiles = self.db.query(DomainExpertProfile).filter(
                DomainExpertProfile.domain_name == domain
            ).all()
            
            if not expert_profiles:
                logger.warning(f"No expert agents found for domain: {domain}")
                return None
            
            # Calculate compatibility scores for each expert
            expert_scores = []
            for profile in expert_profiles:
                agent = self.db.query(UniversityAgent).filter(
                    UniversityAgent.id == profile.agent_id
                ).first()
                
                if not agent or agent.status != "active":
                    continue
                
                score = await self._calculate_expert_compatibility(
                    profile, agent, student_id, learning_profile, specific_requirements
                )
                
                expert_scores.append((agent, profile, score))
            
            # Sort by compatibility score and return the best match
            expert_scores.sort(key=lambda x: x[2], reverse=True)
            
            if expert_scores:
                best_expert = expert_scores[0][0]
                logger.info(f"Assigned expert {best_expert.id} to student {student_id} for {domain}")
                
                # Create assignment record
                await self._create_expert_assignment(student_id, best_expert.id, domain, topic)
                
                return best_expert
            
            logger.warning(f"No suitable expert agent found for student {student_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning expert tutor: {str(e)}")
            return None
    
    async def create_teaching_plan(
        self, 
        expert_id: str, 
        student_id: str, 
        topic: str,
        current_knowledge_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Generate a personalized teaching plan for a student on a specific topic.
        """
        try:
            # Get expert profile and student profile
            expert_profile = self._get_expert_profile(expert_id)
            learning_profile = self._get_student_learning_profile(student_id, expert_profile.domain_name)
            
            # Get relevant knowledge nodes
            knowledge_nodes = self._get_knowledge_nodes(expert_profile.domain_name, topic)
            
            # Generate teaching plan
            teaching_plan = {
                "plan_id": str(uuid.uuid4()),
                "expert_id": expert_id,
                "student_id": student_id,
                "domain": expert_profile.domain_name,
                "topic": topic,
                "current_knowledge_level": current_knowledge_level,
                "estimated_duration_minutes": self._estimate_teaching_duration(knowledge_nodes),
                "learning_objectives": self._extract_learning_objectives(knowledge_nodes),
                "learning_sequence": await self._create_teaching_sequence(
                    knowledge_nodes, learning_profile, expert_profile
                ),
                "adaptation_strategies": self._define_adaptation_strategies(learning_profile),
                "assessment_points": self._define_assessment_points(knowledge_nodes),
                "success_criteria": self._define_success_criteria(knowledge_nodes),
                "created_at": datetime.now(timezone.utc),
                "teaching_style": expert_profile.teaching_style,
                "adaptive_elements": await self._identify_adaptive_elements(learning_profile)
            }
            
            # Store the plan in adaptive learning path
            await self._store_adaptive_learning_path(teaching_plan)
            
            logger.info(f"Created teaching plan {teaching_plan['plan_id']} for expert {expert_id}")
            return teaching_plan
            
        except Exception as e:
            logger.error(f"Error creating teaching plan: {str(e)}")
            return {"error": str(e)}
    
    async def adapt_difficulty(
        self, 
        expert_id: str, 
        student_id: str, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically adjust difficulty based on real-time student performance.
        """
        try:
            # Get current learning path
            learning_path = self._get_active_learning_path(student_id, expert_id)
            if not learning_path:
                return {"error": "No active learning path found"}
            
            # Analyze current performance
            performance_analysis = await self._analyze_performance(performance_data)
            
            # Determine difficulty adjustments
            difficulty_adjustments = await self._determine_difficulty_adjustments(
                performance_analysis, learning_path
            )
            
            # Update learning path
            await self._update_learning_path_difficulty(learning_path, difficulty_adjustments)
            
            # Create adaptation record
            adaptation_record = {
                "adaptation_id": str(uuid.uuid4()),
                "expert_id": expert_id,
                "student_id": student_id,
                "performance_analysis": performance_analysis,
                "difficulty_adjustments": difficulty_adjustments,
                "timestamp": datetime.now(timezone.utc),
                "success_prediction": await self._predict_adaptation_success(difficulty_adjustments)
            }
            
            # Store adaptation in memory
            await self.memory_service.store_learning_insight(
                student_id, 
                f"difficulty_adaptation_{datetime.now().isoformat()}",
                {
                    "type": "difficulty_adaptation",
                    "data": adaptation_record,
                    "context": "real_time_performance_based_adaptation"
                }
            )
            
            return adaptation_record
            
        except Exception as e:
            logger.error(f"Error adapting difficulty: {str(e)}")
            return {"error": str(e)}
    
    async def generate_explanation(
        self, 
        expert_id: str, 
        concept: str, 
        explanation_style: str,
        student_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate explanations in the expert's preferred teaching style.
        """
        try:
            expert_profile = self._get_expert_profile(expert_id)
            
            # Get knowledge node for the concept
            knowledge_node = self._get_knowledge_node_by_concept(
                expert_profile.domain_name, concept
            )
            
            if not knowledge_node:
                # Generate basic explanation using general knowledge
                return await self._generate_basic_explanation(
                    expert_profile, concept, explanation_style, student_context
                )
            
            # Get student learning profile for personalization
            student_profile = None
            if student_context and "student_id" in student_context:
                student_profile = self._get_student_learning_profile(
                    student_context["student_id"], expert_profile.domain_name
                )
            
            # Generate explanation using expert's teaching style
            explanation = await self._construct_explanation(
                knowledge_node, expert_profile, explanation_style, student_profile
            )
            
            # Add adaptive elements based on student profile
            if student_profile:
                explanation = await self._personalize_explanation(
                    explanation, student_profile, knowledge_node
                )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return f"Error generating explanation for {concept}: {str(e)}"
    
    async def create_practice_problems(
        self, 
        expert_id: str, 
        topic: str, 
        difficulty: str,
        count: int = 5,
        problem_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate appropriate practice problems based on topic and difficulty.
        """
        try:
            expert_profile = self._get_expert_profile(expert_id)
            
            # Get relevant knowledge nodes
            knowledge_nodes = self._get_knowledge_nodes(expert_profile.domain_name, topic)
            
            # Generate problems
            problems = []
            for i in range(count):
                problem = await self._generate_single_problem(
                    knowledge_nodes, expert_profile, difficulty, problem_types
                )
                problems.append(problem)
            
            # Add metadata and solutions
            for problem in problems:
                problem.update({
                    "problem_id": str(uuid.uuid4()),
                    "expert_id": expert_id,
                    "topic": topic,
                    "difficulty": difficulty,
                    "generated_at": datetime.now(timezone.utc),
                    "estimated_completion_time_minutes": self._estimate_problem_time(difficulty)
                })
            
            logger.info(f"Generated {len(problems)} practice problems for topic {topic}")
            return problems
            
        except Exception as e:
            logger.error(f"Error creating practice problems: {str(e)}")
            return []
    
    async def assess_understanding(
        self, 
        expert_id: str, 
        student_id: str, 
        responses: Dict[str, Any],
        assessment_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess student understanding and provide detailed feedback.
        """
        try:
            expert_profile = self._get_expert_profile(expert_id)
            learning_profile = self._get_student_learning_profile(student_id, expert_profile.domain_name)
            
            # Perform comprehensive assessment
            assessment_results = {
                "assessment_id": str(uuid.uuid4()),
                "expert_id": expert_id,
                "student_id": student_id,
                "timestamp": datetime.now(timezone.utc),
                "responses_analyzed": len(responses),
                "overall_score": 0.0,
                "concept_scores": {},
                "detailed_feedback": {},
                "areas_of_strength": [],
                "areas_for_improvement": [],
                "recommended_next_steps": [],
                "learning_progress": {}
            }
            
            # Analyze each response
            for question_id, response_data in responses.items():
                question_analysis = await self._analyze_response(
                    question_id, response_data, expert_profile, learning_profile
                )
                assessment_results["concept_scores"][question_id] = question_analysis
            
            # Calculate overall score and learning progress
            scores = [analysis["score"] for analysis in assessment_results["concept_scores"].values()]
            assessment_results["overall_score"] = sum(scores) / len(scores) if scores else 0.0
            
            # Generate detailed feedback
            assessment_results["detailed_feedback"] = await self._generate_detailed_feedback(
                assessment_results, expert_profile, learning_profile
            )
            
            # Identify strengths and improvement areas
            assessment_results["areas_of_strength"] = await self._identify_strengths(assessment_results)
            assessment_results["areas_for_improvement"] = await self._identify_improvements(assessment_results)
            
            # Recommend next steps
            assessment_results["recommended_next_steps"] = await self._recommend_next_steps(
                assessment_results, expert_profile
            )
            
            # Update learning progress
            assessment_results["learning_progress"] = await self._update_learning_progress(
                student_id, assessment_results, learning_profile
            )
            
            # Store assessment in memory
            await self.memory_service.store_learning_insight(
                student_id,
                f"assessment_{assessment_results['assessment_id']}",
                {
                    "type": "performance_assessment",
                    "data": assessment_results,
                    "context": "expert_agent_assessment"
                }
            )
            
            return assessment_results
            
        except Exception as e:
            logger.error(f"Error assessing understanding: {str(e)}")
            return {"error": str(e)}
    
    # ==================== Private Helper Methods ====================
    
    def _get_expert_profile(self, expert_id: str) -> Optional[DomainExpertProfile]:
        """Get expert profile by agent ID"""
        return self.db.query(DomainExpertProfile).filter(
            DomainExpertProfile.agent_id == expert_id
        ).first()
    
    def _get_student_learning_profile(
        self, student_id: str, domain: str
    ) -> Optional[StudentLearningProfile]:
        """Get student learning profile for a specific domain"""
        return self.db.query(StudentLearningProfile).filter(
            and_(
                StudentLearningProfile.agent_id == student_id,
                StudentLearningProfile.domain == domain
            )
        ).first()
    
    def _get_knowledge_nodes(self, domain: str, topic: str) -> List[KnowledgeNode]:
        """Get knowledge nodes for a specific domain and topic"""
        return self.db.query(KnowledgeNode).filter(
            and_(
                KnowledgeNode.domain == domain,
                KnowledgeNode.topic == topic
            )
        ).all()
    
    def _get_knowledge_node_by_concept(
        self, domain: str, concept: str
    ) -> Optional[KnowledgeNode]:
        """Get knowledge node by concept name"""
        return self.db.query(KnowledgeNode).filter(
            and_(
                KnowledgeNode.domain == domain,
                KnowledgeNode.concept_name == concept
            )
        ).first()
    
    async def _calculate_expert_compatibility(
        self, 
        profile: DomainExpertProfile, 
        agent: UniversityAgent,
        student_id: str, 
        learning_profile: Optional[StudentLearningProfile],
        requirements: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate compatibility score between expert and student.
        Higher scores indicate better compatibility.
        """
        score = 0.0
        
        # Base expertise score
        expertise_multipliers = {
            "beginner": 1.0,
            "intermediate": 1.2,
            "advanced": 1.5,
            "expert": 2.0
        }
        score += expertise_multipliers.get(profile.expertise_level, 1.0)
        
        # Success rate bonus
        score += profile.success_rate * 2.0
        
        # Teaching style compatibility
        if learning_profile:
            style_compatibility = await self._assess_teaching_style_compatibility(
                profile, learning_profile
            )
            score += style_compatibility
        
        # Response time bonus (faster = better, capped at 2.0 points)
        response_time_score = max(0, 2.0 - (profile.response_time_seconds / 10.0))
        score += response_time_score
        
        # Historical performance with similar students
        performance_bonus = await self._get_historical_performance_bonus(
            profile.agent_id, student_id, requirements
        )
        score += performance_bonus
        
        return min(score, 10.0)  # Cap at 10.0
    
    async def _assess_teaching_style_compatibility(
        self, 
        profile: DomainExpertProfile, 
        learning_profile: StudentLearningProfile
    ) -> float:
        """Assess compatibility between teaching style and learning style"""
        compatibility_matrix = {
            "visual": {
                "adaptive": 1.5,
                "interactive": 1.3,
                "practical": 1.2,
                "theoretical": 1.0,
                "Socratic": 0.9
            },
            "auditory": {
                "adaptive": 1.4,
                "interactive": 1.5,
                "practical": 1.1,
                "theoretical": 1.3,
                "Socratic": 1.2
            },
            "kinesthetic": {
                "adaptive": 1.5,
                "interactive": 1.4,
                "practical": 1.5,
                "theoretical": 0.8,
                "Socratic": 0.7
            },
            "reading": {
                "adaptive": 1.3,
                "interactive": 1.0,
                "practical": 1.1,
                "theoretical": 1.4,
                "Socratic": 1.1
            },
            "mixed": {
                "adaptive": 1.5,
                "interactive": 1.3,
                "practical": 1.2,
                "theoretical": 1.1,
                "Socratic": 1.0
            }
        }
        
        learning_style = learning_profile.learning_style if learning_profile else "mixed"
        teaching_style = profile.teaching_style if profile.teaching_style else "adaptive"
        
        return compatibility_matrix.get(learning_style, {}).get(teaching_style, 1.0)
    
    async def _get_historical_performance_bonus(
        self, 
        expert_id: str, 
        student_id: str, 
        requirements: Optional[Dict[str, Any]] = None
    ) -> float:
        """Get bonus based on historical performance with similar students"""
        # This would analyze past sessions with similar learning profiles
        # For now, return a small base bonus
        return 0.5
    
    async def _create_expert_assignment(
        self, 
        student_id: str, 
        expert_id: str, 
        domain: str, 
        topic: str
    ):
        """Create expert assignment record"""
        assignment = ExpertSession(
            id=str(uuid.uuid4()),
            expert_agent_id=expert_id,
            student_agent_id=student_id,
            domain=domain,
            topic=topic,
            session_type="tutoring",
            status="active",
            started_at=datetime.now(timezone.utc)
        )
        
        self.db.add(assignment)
        self.db.commit()
    
    def _estimate_teaching_duration(self, knowledge_nodes: List[KnowledgeNode]) -> int:
        """Estimate teaching duration based on knowledge nodes"""
        total_time = sum(node.estimated_learning_time_minutes for node in knowledge_nodes)
        return int(total_time * 1.2)  # Add 20% buffer for discussion and adaptation
    
    def _extract_learning_objectives(self, knowledge_nodes: List[KnowledgeNode]) -> List[str]:
        """Extract learning objectives from knowledge nodes"""
        objectives = []
        for node in knowledge_nodes:
            objectives.extend(node.learning_objectives or [])
        return objectives
    
    async def _create_teaching_sequence(
        self, 
        knowledge_nodes: List[KnowledgeNode], 
        learning_profile: Optional[StudentLearningProfile],
        expert_profile: DomainExpertProfile
    ) -> List[Dict[str, Any]]:
        """Create optimal teaching sequence based on prerequisites and learning style"""
        # Simple implementation - order by prerequisites and estimated time
        sorted_nodes = sorted(
            knowledge_nodes, 
            key=lambda x: (len(x.prerequisites or []), x.estimated_learning_time_minutes)
        )
        
        sequence = []
        for i, node in enumerate(sorted_nodes):
            sequence.append({
                "step": i + 1,
                "concept": node.concept_name,
                "estimated_time_minutes": node.estimated_learning_time_minutes,
                "prerequisites_met": len(node.prerequisites or []),
                "teaching_strategy": await self._select_teaching_strategy(node, expert_profile),
                "adaptation_points": await self._identify_adaptation_points(node, learning_profile)
            })
        
        return sequence
    
    async def _select_teaching_strategy(
        self, 
        node: KnowledgeNode, 
        expert_profile: DomainExpertProfile
    ) -> str:
        """Select optimal teaching strategy for a knowledge node"""
        # Simple implementation - select from available strategies
        strategies = node.teaching_strategies or ["explain", "demonstrate", "practice"]
        return strategies[0] if strategies else "explain"
    
    async def _identify_adaptation_points(
        self, 
        node: KnowledgeNode, 
        learning_profile: Optional[StudentLearningProfile]
    ) -> List[str]:
        """Identify points where adaptation might be needed"""
        adaptations = ["difficulty_check", "comprehension_verification"]
        
        if learning_profile:
            if learning_profile.learning_obstacles:
                adaptations.extend(["obstacle_monitoring", "alternative_explanations"])
        
        return adaptations
    
    def _define_adaptation_strategies(
        self, 
        learning_profile: Optional[StudentLearningProfile]
    ) -> List[Dict[str, Any]]:
        """Define adaptation strategies based on learning profile"""
        strategies = [
            {
                "trigger": "low_comprehension",
                "strategy": "break_down_concept",
                "description": "Break complex concepts into smaller parts"
            },
            {
                "trigger": "high_confidence",
                "strategy": "advance_quickly",
                "description": "Move to advanced concepts when student shows mastery"
            }
        ]
        
        if learning_profile:
            if learning_profile.attention_span_minutes < 30:
                strategies.append({
                    "trigger": "attention_drop",
                    "strategy": "interactive_break",
                    "description": "Insert interactive elements to maintain engagement"
                })
        
        return strategies
    
    def _define_assessment_points(
        self, 
        knowledge_nodes: List[KnowledgeNode]
    ) -> List[Dict[str, Any]]:
        """Define assessment points throughout the teaching sequence"""
        assessments = []
        
        for i, node in enumerate(knowledge_nodes):
            if node.assessment_criteria:
                assessments.append({
                    "point": i + 1,
                    "concept": node.concept_name,
                    "criteria": node.assessment_criteria,
                    "type": "formative" if i < len(knowledge_nodes) - 1 else "summative"
                })
        
        return assessments
    
    def _define_success_criteria(
        self, 
        knowledge_nodes: List[KnowledgeNode]
    ) -> Dict[str, Any]:
        """Define success criteria for the learning session"""
        return {
            "minimum_concepts_mastered": max(1, len(knowledge_nodes) * 0.8),
            "minimum_accuracy": 0.8,
            "engagement_indicators": ["questions_asked", "active_participation"],
            "comprehension_indicators": ["correct_responses", "transfer_ability"]
        }
    
    async def _identify_adaptive_elements(
        self, 
        learning_profile: Optional[StudentLearningProfile]
    ) -> List[str]:
        """Identify adaptive elements based on learning profile"""
        elements = ["real_time_feedback", "difficulty_scaling"]
        
        if learning_profile:
            if learning_profile.learning_style == "visual":
                elements.append("visual_aids")
            elif learning_profile.learning_style == "auditory":
                elements.append("audio_explanations")
            elif learning_profile.learning_style == "kinesthetic":
                elements.append("hands_on_activities")
        
        return elements
    
    async def _store_adaptive_learning_path(self, teaching_plan: Dict[str, Any]):
        """Store teaching plan as adaptive learning path"""
        path = AdaptiveLearningPath(
            id=teaching_plan["plan_id"],
            student_agent_id=teaching_plan["student_id"],
            domain=teaching_plan["domain"],
            path_name=f"{teaching_plan['topic']} - {teaching_plan['expert_id']}",
            path_segments=teaching_plan["learning_sequence"],
            estimated_completion_hours=teaching_plan["estimated_duration_minutes"] / 60.0,
            status="active"
        )
        
        self.db.add(path)
        self.db.commit()
    
    def _get_active_learning_path(
        self, 
        student_id: str, 
        expert_id: str
    ) -> Optional[AdaptiveLearningPath]:
        """Get active learning path for student with expert"""
        return self.db.query(AdaptiveLearningPath).filter(
            and_(
                AdaptiveLearningPath.student_agent_id == student_id,
                AdaptiveLearningPath.status == "active"
            )
        ).first()
    
    async def _analyze_performance(
        self, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze student performance data"""
        return {
            "accuracy_rate": performance_data.get("correct_responses", 0) / max(1, performance_data.get("total_questions", 1)),
            "response_time": performance_data.get("average_response_time", 0),
            "confidence_indicators": performance_data.get("confidence_scores", []),
            "struggle_indicators": performance_data.get("help_requests", 0),
            "engagement_level": performance_data.get("participation_level", 0)
        }
    
    async def _determine_difficulty_adjustments(
        self, 
        performance_analysis: Dict[str, Any], 
        learning_path: AdaptiveLearningPath
    ) -> Dict[str, Any]:
        """Determine difficulty adjustments based on performance"""
        adjustments = {}
        
        if performance_analysis["accuracy_rate"] < 0.6:
            adjustments["decrease_difficulty"] = True
            adjustments["add_practice_rounds"] = True
        elif performance_analysis["accuracy_rate"] > 0.9:
            adjustments["increase_difficulty"] = True
            adjustments["skip_repetition"] = True
        
        if performance_analysis["response_time"] > 30:
            adjustments["simplify_concepts"] = True
        
        if performance_analysis["struggle_indicators"] > 3:
            adjustments["provide_additional_support"] = True
        
        return adjustments
    
    async def _update_learning_path_difficulty(
        self, 
        learning_path: AdaptiveLearningPath, 
        adjustments: Dict[str, Any]
    ):
        """Update learning path difficulty based on adjustments"""
        # Update the adaptation history
        adaptation_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "adjustments": adjustments,
            "reason": "performance_based_adaptation"
        }
        
        current_history = learning_path.adaptation_history or []
        current_history.append(adaptation_entry)
        learning_path.adaptation_history = current_history
        
        self.db.commit()
    
    async def _predict_adaptation_success(
        self, 
        adjustments: Dict[str, Any]
    ) -> float:
        """Predict success probability of proposed adjustments"""
        # Simple prediction based on adjustment types
        base_success = 0.7
        
        if adjustments.get("decrease_difficulty"):
            base_success += 0.1
        if adjustments.get("increase_difficulty"):
            base_success -= 0.05
        if adjustments.get("add_practice_rounds"):
            base_success += 0.05
        

    async def register_expert_agent(self, expert_data: Dict[str, Any]) -> UniversityAgent:
        """Register a new domain expert agent"""
        required_fields = ["name", "domain"]
        for field in required_fields:
            if field not in expert_data:
                raise ValueError(f"Missing required field: {field}")
                
        try:
            agent_id = str(uuid.uuid4())
            
            # Create base agent
            agent = UniversityAgent(
                id=agent_id,
                university_id=str(uuid.uuid4()), # Placeholder university ID
                name=expert_data["name"],
                status="active",
                agent_type="expert",
                configuration={
                    "domain": expert_data["domain"],
                    "capabilities": expert_data.get("available_capabilities", [])
                }
            )
            self.db.add(agent)
            
            # Create expert profile
            profile = DomainExpertProfile(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                domain_name=expert_data["domain"],
                expertise_level=expert_data.get("expertise_level", "expert"),
                specializations=expert_data.get("specializations", []),
                teaching_style=expert_data.get("teaching_style", "adaptive"),
                credentials=expert_data.get("credentials", {}),
                success_rate=0.0,
                total_students_taught=0,
                student_improvement_rate=0.0
            )
            self.db.add(profile)
            
            self.db.commit()
            return agent
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error registering expert agent: {str(e)}")
            raise

    async def get_expert_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get a specific expert agent"""
        agent = self.db.query(UniversityAgent).filter(
            UniversityAgent.id == agent_id
        ).first()
        
        if not agent:
            raise ValueError(f"Expert agent {agent_id} not found")
            
        return {
            "agent_id": agent.id,
            "name": agent.name,
            "domain": agent.configuration.get("domain"),
            "status": agent.status,
            "capabilities": agent.configuration.get("capabilities", [])
        }

    def list_expert_agents(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered expert agents, optionally filtering by domain"""
        query = self.db.query(UniversityAgent).filter(
            UniversityAgent.agent_type == "expert"
        )
        
        if domain:
            # This is a bit tricky with JSON column in SQLite/generic SQLAlchemy without specific dialect support
            # We'll filter in python for safety and simplicity
            agents = query.all()
            filtered_agents = [
                agent for agent in agents 
                if agent.configuration.get("domain") == domain
            ]
            agents = filtered_agents
        else:
            agents = query.all()
            
        return [
            {
                "agent_id": agent.id,
                "name": agent.name,
                "domain": agent.configuration.get("domain"),
                "status": agent.status
            }
            for agent in agents
        ]
    
    async def _construct_explanation(
        self, 
        knowledge_node: KnowledgeNode, 
        expert_profile: DomainExpertProfile,
        explanation_style: str,
        student_profile: Optional[StudentLearningProfile] = None
    ) -> str:
        """Construct explanation based on knowledge node and expert style"""
        # This is a simplified implementation
        # In practice, this would use more sophisticated natural language generation
        
        explanation_parts = []
        
        # Introduction
        explanation_parts.append(f"Let me explain {knowledge_node.concept_name}.")
        
        # Main explanation
        main_explanation = knowledge_node.concept_data.get("explanation", "This is a key concept.")
        explanation_parts.append(main_explanation)
        
        # Examples
        examples = knowledge_node.examples or []
        if examples:
            explanation_parts.append("Here are some examples:")
            for i, example in enumerate(examples[:2], 1):
                explanation_parts.append(f"{i}. {example}")
        
        # Add personalization if available
        if student_profile and student_profile.learning_style == "visual":
            explanation_parts.append("Let me show you a visual representation of this concept.")
        
        return " ".join(explanation_parts)
    
    async def _generate_basic_explanation(
        self, 
        expert_profile: DomainExpertProfile, 
        concept: str, 
        style: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate basic explanation when no knowledge node exists"""
        # Simple fallback explanation
        templates = {
            "Socratic": f"What do you think {concept} means? Let's explore this together.",
            "practical": f"Here's how {concept} applies in real-world situations:",
            "theoretical": f"The theoretical understanding of {concept} involves:",
            "interactive": f"Let's learn about {concept} through hands-on exploration!",
            "adaptive": f"I'll explain {concept} in a way that works best for you."
        }
        
        base_explanation = templates.get(style, f"Let me explain {concept}.")
        
        if context and "difficulty_level" in context:
            if context["difficulty_level"] == "beginner":
                base_explanation += " I'll keep it simple and clear."
            elif context["difficulty_level"] == "advanced":
                base_explanation += " I'll go into more depth with this explanation."
        
        return base_explanation
    
    async def _personalize_explanation(
        self, 
        explanation: str, 
        learning_profile: StudentLearningProfile,
        knowledge_node: KnowledgeNode
    ) -> str:
        """Personalize explanation based on student learning profile"""
        personalized_explanation = explanation
        
        # Add learning style specific elements
        if learning_profile.learning_style == "visual":
            personalized_explanation += " [Visual aid would be shown here]"
        elif learning_profile.learning_style == "auditory":
            personalized_explanation += " [Audio explanation would be provided here]"
        
        # Consider attention span
        if learning_profile.attention_span_minutes < 30:
            personalized_explanation += " Let's break this into shorter sections."
        
        return personalized_explanation
    
    def _estimate_problem_time(self, difficulty: str) -> int:
        """Estimate problem completion time based on difficulty"""
        time_mapping = {
            "beginner": 10,
            "intermediate": 15,
            "advanced": 25,
            "expert": 40
        }
        return time_mapping.get(difficulty, 15)
    
    async def _generate_single_problem(
        self, 
        knowledge_nodes: List[KnowledgeNode], 
        expert_profile: DomainExpertProfile,
        difficulty: str,
        problem_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a single practice problem"""
        # Simplified problem generation
        if not knowledge_nodes:
            # Generate generic problem
            return {
                "type": "conceptual",
                "question": f"Explain the key concept of {expert_profile.domain_name}.",
                "solution": "Provide a comprehensive explanation.",
                "difficulty": difficulty,
                "estimated_time": self._estimate_problem_time(difficulty)
            }
        
        # Use first knowledge node as basis
        base_node = knowledge_nodes[0]
        
        return {
            "type": "application",
            "question": f"Apply the concept of {base_node.concept_name} to solve this problem.",
            "solution": f"The solution involves understanding {base_node.concept_name}.",
            "difficulty": difficulty,
            "concept": base_node.concept_name,
            "estimated_time": self._estimate_problem_time(difficulty)
        }
    
    async def _analyze_response(
        self, 
        question_id: str, 
        response_data: Dict[str, Any],
        expert_profile: DomainExpertProfile,
        learning_profile: Optional[StudentLearningProfile]
    ) -> Dict[str, Any]:
        """Analyze a single student response"""
        return {
            "question_id": question_id,
            "score": response_data.get("score", 0.5),
            "correctness": response_data.get("is_correct", False),
            "completeness": response_data.get("completeness", 0.5),
            "clarity": response_data.get("clarity", 0.5),
            "response_time": response_data.get("response_time", 0),
            "confidence": response_data.get("confidence", 0.5)
        }
    
    async def _generate_detailed_feedback(
        self, 
        assessment_results: Dict[str, Any],
        expert_profile: DomainExpertProfile,
        learning_profile: Optional[StudentLearningProfile]
    ) -> Dict[str, Any]:
        """Generate detailed feedback for the assessment"""
        feedback = {
            "positive_feedback": [],
            "constructive_feedback": [],
            "next_steps": []
        }
        
        # Generate feedback based on scores
        if assessment_results["overall_score"] > 0.8:
            feedback["positive_feedback"].append("Excellent understanding demonstrated!")
        elif assessment_results["overall_score"] > 0.6:
            feedback["positive_feedback"].append("Good progress made!")
        
        if assessment_results["overall_score"] < 0.6:
            feedback["constructive_feedback"].append("Consider reviewing the foundational concepts.")
        
        return feedback
    
    async def _identify_strengths(
        self, 
        assessment_results: Dict[str, Any]
    ) -> List[str]:
        """Identify areas of strength"""
        strengths = []
        
        # Analyze concept scores
        for concept, data in assessment_results["concept_scores"].items():
            if data["score"] > 0.8:
                strengths.append(f"Strong understanding of {concept}")
        
        return strengths
    
    async def _identify_improvements(
        self, 
        assessment_results: Dict[str, Any]
    ) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        # Analyze concept scores
        for concept, data in assessment_results["concept_scores"].items():
            if data["score"] < 0.6:
                improvements.append(f"Needs practice with {concept}")
        
        return improvements
    
    async def _recommend_next_steps(
        self, 
        assessment_results: Dict[str, Any],
        expert_profile: DomainExpertProfile
    ) -> List[str]:
        """Recommend next steps for learning"""
        next_steps = []
        
        # Base recommendations on overall score
        if assessment_results["overall_score"] > 0.8:
            next_steps.append("Ready to move to more advanced concepts")
        elif assessment_results["overall_score"] < 0.6:
            next_steps.append("Review fundamental concepts before proceeding")
        
        # Add domain-specific recommendations
        if expert_profile.domain_name == "mathematics":
            next_steps.append("Practice with additional problem sets")
        elif expert_profile.domain_name == "science":
            next_steps.append("Apply concepts through hands-on experiments")
        
        return next_steps
    
    async def _update_learning_progress(
        self, 
        student_id: str, 
        assessment_results: Dict[str, Any],
        learning_profile: Optional[StudentLearningProfile]
    ) -> Dict[str, Any]:
        """Update learning progress tracking"""
        progress_data = {
            "last_assessment_score": assessment_results["overall_score"],
            "concepts_mastered": len(assessment_results["areas_of_strength"]),
            "concepts_needing_practice": len(assessment_results["areas_for_improvement"]),
            "improvement_trend": "positive" if assessment_results["overall_score"] > 0.7 else "needs_work",
            "next_assessment_recommended": True
        }
        
        return progress_data