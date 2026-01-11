"""
Knowledge Sharing Framework

This module enables intelligent knowledge sharing between agents including:
- Identifying knowledge gaps
- Matching knowledge sources with needs
- Facilitating teaching sessions
- Validating knowledge transfer
- Encouraging spontaneous sharing
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid
import logging
from dryad.university.database.models_university import (
    UniversityAgent, KnowledgeSharing, DomainExpertProfile, 
    KnowledgeEntity, LearningContext
)

logger = logging.getLogger(__name__)

class KnowledgeSharingFramework:
    """Enables intelligent knowledge sharing between agents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def identify_knowledge_gaps(self, agent_id: str) -> List[Dict[str, Any]]:
        """Identify what knowledge an agent needs
        
        Args:
            agent_id: ID of the agent to analyze
            
        Returns:
            List of knowledge gaps with priority and context
        """
        try:
            # Get agent profile and current knowledge
            agent_profile = self._get_agent_profile(agent_id)
            current_knowledge = self._get_agent_knowledge(agent_id)
            learning_history = self._get_learning_history(agent_id)
            
            # Identify gaps based on multiple factors
            knowledge_gaps = []
            
            # 1. Curriculum-based gaps
            curriculum_gaps = self._identify_curriculum_gaps(agent_id, agent_profile)
            knowledge_gaps.extend(curriculum_gaps)
            
            # 2. Skill-based gaps
            skill_gaps = self._identify_skill_gaps(agent_id, agent_profile, current_knowledge)
            knowledge_gaps.extend(skill_gaps)
            
            # 3. Domain expertise gaps
            expertise_gaps = self._identify_expertise_gaps(agent_id, agent_profile)
            knowledge_gaps.extend(expertise_gaps)
            
            # 4. Collaboration-based gaps
            collaboration_gaps = self._identify_collaboration_gaps(agent_id, learning_history)
            knowledge_gaps.extend(collaboration_gaps)
            
            # 5. Goal-oriented gaps
            goal_gaps = self._identify_goal_oriented_gaps(agent_id, agent_profile)
            knowledge_gaps.extend(goal_gaps)
            
            # Prioritize gaps
            prioritized_gaps = self._prioritize_knowledge_gaps(knowledge_gaps)
            
            logger.info(f"Identified {len(prioritized_gaps)} knowledge gaps for agent {agent_id}")
            return prioritized_gaps
            
        except Exception as e:
            logger.error(f"Error identifying knowledge gaps for agent {agent_id}: {e}")
            return []
    
    def match_knowledge_sources(self, needer_id: str, expertise_required: str) -> List[str]:
        """Find agents with relevant expertise
        
        Args:
            needer_id: ID of the agent needing knowledge
            expertise_required: Type of expertise needed
            
        Returns:
            List of agent IDs with matching expertise, ranked by relevance
        """
        try:
            # Get agents with the required expertise
            expert_agents = self._find_expert_agents(expertise_required)
            
            # Filter out the needer agent
            available_experts = [agent for agent in expert_agents if agent != needer_id]
            
            # Score and rank experts
            ranked_experts = self._rank_expert_sources(
                needer_id, available_experts, expertise_required
            )
            
            logger.info(f"Found {len(ranked_experts)} expert sources for agent {needer_id}")
            return ranked_experts
            
        except Exception as e:
            logger.error(f"Error matching knowledge sources: {e}")
            return []
    
    def facilitate_teaching_sessions(self, teacher_id: str, student_id: str, 
                                   topic: str) -> Dict[str, Any]:
        """Organize structured teaching sessions between agents
        
        Args:
            teacher_id: ID of the agent teaching
            student_id: ID of the agent learning
            topic: Topic to be taught
            
        Returns:
            Dictionary containing session plan and details
        """
        try:
            # Get profiles for both agents
            teacher_profile = self._get_agent_profile(teacher_id)
            student_profile = self._get_agent_profile(student_id)
            
            # Analyze topic requirements
            topic_analysis = self._analyze_topic_requirements(topic)
            
            # Check compatibility
            compatibility = self._assess_teaching_compatibility(
                teacher_profile, student_profile, topic_analysis
            )
            
            if compatibility['compatibility_score'] < 0.5:
                logger.warning(f"Low teaching compatibility between {teacher_id} and {student_id}")
                return {'status': 'incompatible', 'reason': compatibility['issues']}
            
            # Create teaching session plan
            session_plan = self._create_teaching_session_plan(
                teacher_profile, student_profile, topic_analysis, compatibility
            )
            
            # Validate session feasibility
            feasibility_check = self._validate_session_feasibility(session_plan)
            
            if not feasibility_check['feasible']:
                return {
                    'status': 'infeasible',
                    'issues': feasibility_check['issues'],
                    'suggestions': feasibility_check['suggestions']
                }
            
            # Create session record
            session_record = {
                'session_id': str(uuid.uuid4()),
                'teacher_id': teacher_id,
                'student_id': student_id,
                'topic': topic,
                'session_plan': session_plan,
                'status': 'planned',
                'created_at': datetime.now(timezone.utc)
            }
            
            # Schedule session
            scheduled_session = self._schedule_teaching_session(session_record)
            
            logger.info(f"Facilitated teaching session between {teacher_id} and {student_id} for topic {topic}")
            return {
                'status': 'success',
                'session': scheduled_session,
                'compatibility_score': compatibility['compatibility_score']
            }
            
        except Exception as e:
            logger.error(f"Error facilitating teaching session: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def validate_knowledge_transfer(self, transfer_id: str) -> bool:
        """Verify that knowledge was successfully transferred
        
        Args:
            transfer_id: ID of the knowledge sharing record
            
        Returns:
            Boolean indicating successful validation
        """
        try:
            # Get knowledge sharing record
            transfer_record = self.db.query(KnowledgeSharing).filter(
                KnowledgeSharing.id == transfer_id
            ).first()
            
            if not transfer_record:
                logger.error(f"Knowledge transfer record {transfer_id} not found")
                return False
            
            # Get teaching/learning context
            teacher_id = transfer_record.sharing_agent_id
            student_id = transfer_record.receiving_agent_id
            
            # Assess knowledge comprehension
            comprehension_assessment = self._assess_knowledge_comprehension(
                student_id, transfer_record.knowledge_content
            )
            
            # Update transfer record with validation results
            transfer_record.comprehension_verified = comprehension_assessment['verified']
            transfer_record.feedback_quality = comprehension_assessment['quality_score']
            transfer_record.adoption_success = comprehension_assessment['adoption_score']
            
            self.db.commit()
            
            logger.info(f"Validated knowledge transfer {transfer_id}: {comprehension_assessment['verified']}")
            return comprehension_assessment['verified']
            
        except Exception as e:
            logger.error(f"Error validating knowledge transfer: {e}")
            return False
    
    def encourage_spontaneous_sharing(self, agent_id: str, opportunity: str) -> bool:
        """Encourage agents to share insights spontaneously
        
        Args:
            agent_id: ID of the agent to encourage
            opportunity: Context or opportunity for sharing
            
        Returns:
            Boolean indicating success of encouragement
        """
        try:
            # Analyze opportunity for sharing
            opportunity_analysis = self._analyze_sharing_opportunity(opportunity)
            
            # Get agent's sharing readiness
            sharing_readiness = self._assess_sharing_readiness(agent_id)
            
            # Generate sharing prompts
            sharing_prompts = self._generate_sharing_prompts(
                agent_id, opportunity_analysis, sharing_readiness
            )
            
            # Create sharing notification
            sharing_notification = {
                'agent_id': agent_id,
                'type': 'spontaneous_sharing_opportunity',
                'opportunity': opportunity_analysis,
                'prompts': sharing_prompts,
                'readiness_score': sharing_readiness['readiness_score'],
                'timestamp': datetime.now(timezone.utc)
            }
            
            # Log the encouragement opportunity
            logger.info(f"Encouraged spontaneous sharing for agent {agent_id} during {opportunity}")
            
            # In a real implementation, this would send a notification to the agent
            return True
            
        except Exception as e:
            logger.error(f"Error encouraging spontaneous sharing: {e}")
            return False
    
    def track_knowledge_ecosystem(self, university_id: str) -> Dict[str, Any]:
        """Track the overall knowledge ecosystem within a university
        
        Args:
            university_id: ID of the university
            
        Returns:
            Dictionary containing ecosystem analysis and health metrics
        """
        try:
            # Get all agents in the university
            university_agents = self.db.query(UniversityAgent).filter(
                UniversityAgent.university_id == university_id
            ).all()
            
            agent_ids = [agent.id for agent in university_agents]
            
            # Analyze knowledge distribution
            knowledge_distribution = self._analyze_knowledge_distribution(agent_ids)
            
            # Analyze knowledge sharing patterns
            sharing_patterns = self._analyze_sharing_patterns(agent_ids)
            
            # Identify knowledge clusters and gaps
            knowledge_clusters = self._identify_knowledge_clusters(agent_ids)
            knowledge_gaps = self._identify_ecosystem_gaps(agent_ids)
            
            # Calculate ecosystem health
            ecosystem_health = self._calculate_ecosystem_health({
                'knowledge_distribution': knowledge_distribution,
                'sharing_patterns': sharing_patterns,
                'clusters': knowledge_clusters,
                'gaps': knowledge_gaps
            })
            
            # Generate recommendations
            recommendations = self._generate_ecosystem_recommendations(ecosystem_health)
            
            return {
                'university_id': university_id,
                'total_agents': len(agent_ids),
                'knowledge_distribution': knowledge_distribution,
                'sharing_patterns': sharing_patterns,
                'knowledge_clusters': knowledge_clusters,
                'knowledge_gaps': knowledge_gaps,
                'ecosystem_health': ecosystem_health,
                'recommendations': recommendations,
                'analysis_timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error tracking knowledge ecosystem: {e}")
            return {}
    
    # Helper methods
    
    def _get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent profile"""
        agent = self.db.query(UniversityAgent).filter(
            UniversityAgent.id == agent_id
        ).first()
        
        if not agent:
            return {}
        
        # Get domain expert profile
        expert_profile = self.db.query(DomainExpertProfile).filter(
            DomainExpertProfile.agent_id == agent_id
        ).first()
        
        return {
            'basic_info': {
                'id': agent.id,
                'name': agent.name,
                'agent_type': agent.agent_type,
                'specialization': agent.specialization,
                'competency_score': agent.competency_score,
                'elo_rating': agent.elo_rating
            },
            'expertise': expert_profile.knowledge_base if expert_profile else {},
            'teaching_style': expert_profile.teaching_style if expert_profile else 'adaptive',
            'available_capabilities': expert_profile.available_capabilities if expert_profile else []
        }
    
    def _get_agent_knowledge(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get agent's current knowledge entities"""
        knowledge_entities = self.db.query(KnowledgeEntity).filter(
            KnowledgeEntity.agent_id == agent_id
        ).all()
        
        return [
            {
                'entity_type': entity.entity_type,
                'entity_name': entity.entity_name,
                'confidence': entity.confidence,
                'created_at': entity.created_at
            }
            for entity in knowledge_entities
        ]
    
    def _get_learning_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get agent's learning history and context"""
        learning_contexts = self.db.query(LearningContext).filter(
            LearningContext.agent_id == agent_id
        ).all()
        
        return [
            {
                'context_type': context.context_type,
                'success_patterns': context.success_patterns,
                'failure_patterns': context.failure_patterns,
                'confidence_score': context.confidence_score,
                'created_at': context.created_at
            }
            for context in learning_contexts
        ]
    
    def _identify_curriculum_gaps(self, agent_id: str, agent_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify knowledge gaps based on curriculum progression"""
        # This would integrate with curriculum system
        # For now, return placeholder gaps
        return [
            {
                'gap_type': 'curriculum',
                'knowledge_area': 'Mathematics',
                'specific_topic': 'Calculus II',
                'priority': 'high',
                'estimated_learning_time': 40,
                'prerequisites_met': True
            }
        ]
    
    def _identify_skill_gaps(self, agent_id: str, agent_profile: Dict[str, Any], 
                           current_knowledge: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify gaps based on skill requirements"""
        # Analyze current skills vs required skills
        return [
            {
                'gap_type': 'skill',
                'skill_area': 'Critical Thinking',
                'specific_skill': 'Problem Analysis',
                'priority': 'medium',
                'learning_method': 'practice',
                'estimated_time': 20
            }
        ]
    
    def _identify_expertise_gaps(self, agent_id: str, agent_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify gaps in domain expertise"""
        current_expertise = set(agent_profile.get('expertise', {}).keys())
        # Define what expertise areas are important for the agent type
        required_expertise = self._get_required_expertise_for_agent_type(
            agent_profile['basic_info']['agent_type']
        )
        
        missing_expertise = required_expertise - current_expertise
        
        gaps = []
        for expertise_area in missing_expertise:
            gaps.append({
                'gap_type': 'expertise',
                'knowledge_area': expertise_area,
                'priority': 'medium',
                'learning_method': 'mentorship',
                'estimated_time': 60
            })
        
        return gaps
    
    def _identify_collaboration_gaps(self, agent_id: str, learning_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify gaps in collaboration skills"""
        # Analyze collaboration performance from learning history
        return [
            {
                'gap_type': 'collaboration',
                'skill_area': 'Team Communication',
                'specific_skill': 'Active Listening',
                'priority': 'medium',
                'learning_method': 'peer_learning',
                'estimated_time': 15
            }
        ]
    
    def _identify_goal_oriented_gaps(self, agent_id: str, agent_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify gaps based on agent goals and objectives"""
        # This would integrate with goal-setting system
        return []
    
    def _prioritize_knowledge_gaps(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize knowledge gaps based on multiple factors"""
        # Sort by priority and estimated time
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        
        sorted_gaps = sorted(gaps, key=lambda x: (
            priority_order.get(x.get('priority', 'low'), 1),
            -x.get('estimated_time', 0)
        ), reverse=True)
        
        return sorted_gaps
    
    def _get_required_expertise_for_agent_type(self, agent_type: str) -> set:
        """Get required expertise areas for an agent type"""
        expertise_map = {
            'student': {'study_skills', 'basic_research', 'communication'},
            'professor': {'teaching', 'research', 'curriculum_design'},
            'researcher': {'research_methods', 'data_analysis', 'publication'},
            'administrator': {'leadership', 'management', 'policy'}
        }
        
        return expertise_map.get(agent_type, set())
    
    def _find_expert_agents(self, expertise_required: str) -> List[str]:
        """Find agents with specific expertise"""
        expert_profiles = self.db.query(DomainExpertProfile).filter(
            or_(
                DomainExpertProfile.domain_name == expertise_required,
                DomainExpertProfile.knowledge_base.contains({expertise_required: {}})
            )
        ).all()
        
        return [profile.agent_id for profile in expert_profiles]
    
    def _rank_expert_sources(self, needer_id: str, available_experts: List[str], 
                           expertise_required: str) -> List[str]:
        """Rank expert sources by relevance and availability"""
        expert_scores = []
        
        for expert_id in available_experts:
            expert_profile = self._get_agent_profile(expert_id)
            
            # Calculate relevance score
            relevance_score = 0.0
            
            # Check domain expertise
            if expertise_required in expert_profile.get('expertise', {}):
                relevance_score += 0.5
            
            # Check teaching effectiveness
            if expert_profile.get('teaching_style'):
                relevance_score += 0.3
            
            # Check availability (simulated)
            relevance_score += 0.2  # Availability bonus
            
            expert_scores.append((expert_id, relevance_score))
        
        # Sort by score descending
        ranked_experts = [expert_id for expert_id, score in 
                         sorted(expert_scores, key=lambda x: x[1], reverse=True)]
        
        return ranked_experts
    
    def _analyze_topic_requirements(self, topic: str) -> Dict[str, Any]:
        """Analyze requirements for teaching a specific topic"""
        # This would integrate with knowledge base system
        return {
            'topic': topic,
            'complexity_level': 'intermediate',
            'prerequisites': [],
            'learning_objectives': [
                f"Understand basic concepts of {topic}",
                f"Apply {topic} in practical scenarios",
                f"Evaluate {topic} effectiveness"
            ],
            'estimated_duration': 60,
            'teaching_methods': ['discussion', 'examples', 'practice']
        }
    
    def _assess_teaching_compatibility(self, teacher_profile: Dict[str, Any], 
                                     student_profile: Dict[str, Any], 
                                     topic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compatibility between teacher and student for topic"""
        compatibility_score = 0.7  # Default score
        
        issues = []
        
        # Check teacher's expertise in topic
        if topic_analysis['topic'] not in teacher_profile.get('expertise', {}):
            compatibility_score -= 0.3
            issues.append("Teacher lacks expertise in topic")
        
        # Check student readiness
        if student_profile['basic_info']['competency_score'] < 0.5:
            compatibility_score -= 0.2
            issues.append("Student may not be ready for this topic")
        
        return {
            'compatibility_score': max(compatibility_score, 0.0),
            'issues': issues,
            'recommendations': ["Consider prerequisite review"] if issues else []
        }
    
    def _create_teaching_session_plan(self, teacher_profile: Dict[str, Any], 
                                    student_profile: Dict[str, Any], 
                                    topic_analysis: Dict[str, Any], 
                                    compatibility: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed teaching session plan"""
        return {
            'session_id': str(uuid.uuid4()),
            'duration_minutes': topic_analysis['estimated_duration'],
            'phases': [
                {
                    'phase': 'introduction',
                    'duration_minutes': 10,
                    'objectives': ['Introduce topic', 'Assess prior knowledge'],
                    'methods': ['questioning', 'discussion']
                },
                {
                    'phase': 'core_teaching',
                    'duration_minutes': 35,
                    'objectives': topic_analysis['learning_objectives'],
                    'methods': topic_analysis['teaching_methods']
                },
                {
                    'phase': 'practice',
                    'duration_minutes': 10,
                    'objectives': ['Apply knowledge', 'Reinforce learning'],
                    'methods': ['exercises', 'review']
                },
                {
                    'phase': 'assessment',
                    'duration_minutes': 5,
                    'objectives': ['Verify understanding', 'Plan follow-up'],
                    'methods': ['questions', 'feedback']
                }
            ],
            'resources_needed': ['examples', 'exercises', 'assessment_tools'],
            'adaptation_points': ['Difficulty adjustment', 'Pace modification']
        }
    
    def _validate_session_feasibility(self, session_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a teaching session is feasible"""
        issues = []
        suggestions = []
        
        # Check duration
        if session_plan['duration_minutes'] > 120:
            issues.append("Session duration too long")
            suggestions.append("Split into multiple sessions")
        
        # Check phase balance
        total_time = sum(phase['duration_minutes'] for phase in session_plan['phases'])
        if total_time != session_plan['duration_minutes']:
            issues.append("Phase durations don't sum to total session time")
        
        return {
            'feasible': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _schedule_teaching_session(self, session_record: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a teaching session"""
        # In real implementation, this would integrate with scheduling system
        scheduled_session = {
            **session_record,
            'scheduled_start': datetime.now(timezone.utc),
            'status': 'scheduled'
        }
        
        return scheduled_session
    
    def _assess_knowledge_comprehension(self, student_id: str, 
                                      knowledge_content: Dict[str, Any]) -> Dict[str, Any]:
        """Assess student comprehension of shared knowledge"""
        # This would involve testing student's understanding
        # For now, simulate assessment
        
        return {
            'verified': True,  # Simulated success
            'quality_score': 0.8,
            'adoption_score': 0.75,
            'assessment_method': 'simulated_test',
            'areas_strong': ['basic_concepts'],
            'areas_needing_improvement': ['advanced_applications']
        }
    
    def _analyze_sharing_opportunity(self, opportunity: str) -> Dict[str, Any]:
        """Analyze an opportunity for knowledge sharing"""
        return {
            'opportunity_type': 'collaborative_project',
            'context': opportunity,
            'sharing_potential': 0.8,
            'relevant_knowledge_areas': ['problem_solving', 'analysis'],
            'urgency': 'medium'
        }
    
    def _assess_sharing_readiness(self, agent_id: str) -> Dict[str, Any]:
        """Assess agent's readiness for knowledge sharing"""
        # This would analyze agent's knowledge, availability, and sharing tendency
        return {
            'readiness_score': 0.7,
            'knowledge_available': True,
            'time_available': True,
            'sharing_tendency': 'medium',
            'recent_sharing_activity': 3  # Number of recent sharing instances
        }
    
    def _generate_sharing_prompts(self, agent_id: str, opportunity_analysis: Dict[str, Any], 
                                readiness: Dict[str, Any]) -> List[str]:
        """Generate prompts to encourage sharing"""
        prompts = []
        
        if opportunity_analysis['sharing_potential'] > 0.7:
            prompts.append("You have valuable insights that could help your peers")
            prompts.append("This collaboration could benefit from your expertise")
        
        if readiness['sharing_tendency'] == 'medium':
            prompts.append("Consider sharing your recent learning experiences")
        
        return prompts
    
    def _analyze_knowledge_distribution(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze knowledge distribution across agents"""
        all_knowledge = {}
        
        for agent_id in agent_ids:
            agent_knowledge = self._get_agent_knowledge(agent_id)
            all_knowledge[agent_id] = agent_knowledge
        
        # Calculate distribution metrics
        knowledge_areas = {}
        for agent_id, knowledge_list in all_knowledge.items():
            for knowledge in knowledge_list:
                area = knowledge['entity_type']
                if area not in knowledge_areas:
                    knowledge_areas[area] = []
                knowledge_areas[area].append(agent_id)
        
        return {
            'total_knowledge_entities': sum(len(k) for k in all_knowledge.values()),
            'knowledge_coverage': {area: len(agents) for area, agents in knowledge_areas.items()},
            'distribution_balance': len(set(len(v) for v in knowledge_areas.values())) == 1
        }
    
    def _analyze_sharing_patterns(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Analyze knowledge sharing patterns"""
        # Get all knowledge sharing records
        sharing_records = self.db.query(KnowledgeSharing).filter(
            or_(
                KnowledgeSharing.sharing_agent_id.in_(agent_ids),
                KnowledgeSharing.receiving_agent_id.in_(agent_ids)
            )
        ).all()
        
        # Analyze patterns
        sharing_by_agent = {}
        receiving_by_agent = {}
        
        for record in sharing_records:
            if record.sharing_agent_id in agent_ids:
                sharing_by_agent[record.sharing_agent_id] = sharing_by_agent.get(record.sharing_agent_id, 0) + 1
            
            if record.receiving_agent_id in agent_ids:
                receiving_by_agent[record.receiving_agent_id] = receiving_by_agent.get(record.receiving_agent_id, 0) + 1
        
        return {
            'total_sharing_events': len(sharing_records),
            'sharing_activity': sharing_by_agent,
            'receiving_activity': receiving_by_agent,
            'sharing_balance': len(sharing_by_agent) == len(receiving_by_agent)
        }
    
    def _identify_knowledge_clusters(self, agent_ids: List[str]) -> List[Dict[str, Any]]:
        """Identify clusters of agents with similar knowledge"""
        # Simple clustering based on knowledge entities
        clusters = []
        
        # Group agents by primary knowledge areas
        knowledge_groups = {}
        
        for agent_id in agent_ids:
            agent_knowledge = self._get_agent_knowledge(agent_id)
            if agent_knowledge:
                primary_area = agent_knowledge[0]['entity_type']
                if primary_area not in knowledge_groups:
                    knowledge_groups[primary_area] = []
                knowledge_groups[primary_area].append(agent_id)
        
        for area, agents in knowledge_groups.items():
            if len(agents) > 1:
                clusters.append({
                    'cluster_id': str(uuid.uuid4()),
                    'knowledge_area': area,
                    'agents': agents,
                    'size': len(agents),
                    'strength': len(agents) / len(agent_ids)
                })
        
        return clusters
    
    def _identify_ecosystem_gaps(self, agent_ids: List[str]) -> List[Dict[str, Any]]:
        """Identify gaps in the knowledge ecosystem"""
        gaps = []
        
        # Check for knowledge areas with no coverage
        all_knowledge_types = set()
        for agent_id in agent_ids:
            agent_knowledge = self._get_agent_knowledge(agent_id)
            all_knowledge_types.update(k['entity_type'] for k in agent_knowledge)
        
        # Identify uncovered knowledge types (this would need external knowledge of important types)
        important_knowledge_types = {'critical_thinking', 'collaboration', 'creativity', 'analysis'}
        uncovered = important_knowledge_types - all_knowledge_types
        
        for knowledge_type in uncovered:
            gaps.append({
                'gap_id': str(uuid.uuid4()),
                'knowledge_type': knowledge_type,
                'agents_needed': 2,
                'priority': 'high',
                'estimated_impact': 'high'
            })
        
        return gaps
    
    def _calculate_ecosystem_health(self, ecosystem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall health of knowledge ecosystem"""
        health_score = 0.0
        
        # Distribution health
        if ecosystem_data['knowledge_distribution']['distribution_balance']:
            health_score += 0.3
        
        # Sharing health
        if ecosystem_data['sharing_patterns']['sharing_balance']:
            health_score += 0.3
        
        # Coverage health
        coverage_ratio = len(ecosystem_data['knowledge_distribution']['knowledge_coverage']) / 10.0
        health_score += min(coverage_ratio, 0.2)
        
        # Gap penalty
        gap_penalty = len(ecosystem_data['gaps']) * 0.05
        health_score = max(health_score - gap_penalty, 0.0)
        
        return {
            'overall_score': health_score,
            'distribution_health': 0.8 if ecosystem_data['knowledge_distribution']['distribution_balance'] else 0.5,
            'sharing_health': 0.7 if ecosystem_data['sharing_patterns']['sharing_balance'] else 0.4,
            'coverage_health': min(coverage_ratio, 1.0),
            'gap_health': max(1.0 - gap_penalty, 0.0)
        }
    
    def _generate_ecosystem_recommendations(self, ecosystem_health: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate recommendations to improve ecosystem health"""
        recommendations = []
        
        if ecosystem_health['distribution_health'] < 0.6:
            recommendations.append({
                'area': 'distribution',
                'action': 'Encourage cross-pollination of knowledge',
                'priority': 'high'
            })
        
        if ecosystem_health['sharing_health'] < 0.6:
            recommendations.append({
                'area': 'sharing',
                'action': 'Implement knowledge sharing incentives',
                'priority': 'high'
            })
        
        if ecosystem_health['coverage_health'] < 0.7:
            recommendations.append({
                'area': 'coverage',
                'action': 'Expand knowledge base coverage',
                'priority': 'medium'
            })
        
        return recommendations