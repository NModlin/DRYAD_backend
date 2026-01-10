"""
History Expert Agent

Specialized in history education and historical analysis:
- Historical analysis and interpretation with multiple perspectives
- Critical thinking about historical sources and evidence
- Timeline construction and chronological analysis
- Comparative historical studies and pattern recognition
- Understanding historical causation and consequence relationships
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
import logging
from datetime import datetime, timezone
import re
from collections import defaultdict

from app.university_system.database.models_university import (
    UniversityAgent, DomainExpertProfile, ExpertSession, KnowledgeNode,
    TeachingMethod, StudentLearningProfile
)
from app.university_system.services.domain_expert_engine import DomainExpertEngine
from app.university_system.services.adaptive_learning import AdaptiveLearningSystem

logger = logging.getLogger(__name__)

class HistoryExpertAgent:
    """
    Specialized history expert agent capable of tutoring across multiple historical periods and regions:
    - Ancient History: Classical civilizations, early empires, ancient cultures
    - Medieval History: Middle Ages, feudalism, religious and secular conflicts
    - Modern History: Renaissance, Reformation, Age of Exploration, Enlightenment
    - Contemporary History: Industrial Revolution, World Wars, Cold War, Globalization
    - Regional Histories: European, American, Asian, African, Latin American, Middle Eastern
    - Thematic History: Economic, social, political, cultural, intellectual, technological
    """
    
    def __init__(self, db: Session, expert_engine: DomainExpertEngine, adaptive_system: AdaptiveLearningSystem):
        self.db = db
        self.expert_engine = expert_engine
        self.adaptive_system = adaptive_system
        self.domain = "history"
        
        # Historical periods and their key characteristics
        self.historical_periods = {
            "ancient_history": {
                "time_range": "3000 BCE - 500 CE",
                "key_civilizations": ["mesopotamia", "egypt", "greece", "rome", "china", "india"],
                "major_themes": ["civilization_emergence", "empire_building", "philosophical_development"],
                "primary_sources": ["inscriptions", "artifacts", "literature", "archaeological_evidence"],
                "historical_skills": ["chronological_thinking", "historical_analysis", "source_evaluation"]
            },
            "medieval_history": {
                "time_range": "500 - 1500 CE",
                "key_civilizations": ["byzantine", "islamic", "feudal_europe", "mongol_empire", "ming_china"],
                "major_themes": ["feudalism", "religious_influence", "cultural_exchange", "technological_change"],
                "primary_sources": ["chronicles", "religious_texts", "legal_codes", "artistic_works"],
                "historical_skills": ["contextual_understanding", "multiple_perspectives", "cause_effect_analysis"]
            },
            "early_modern": {
                "time_range": "1500 - 1800 CE",
                "key_civilizations": ["european_nations", "ottoman_empire", "ming_qing_china", "mughal_india"],
                "major_themes": ["renaissance", "reformation", "exploration", "colonization", "enlightenment"],
                "primary_sources": ["explorers_accounts", "colonial_records", "philosophical_works", "artistic_productions"],
                "historical_skills": ["comparative_analysis", "continuity_change", "historical_argumentation"]
            },
            "modern_history": {
                "time_range": "1800 - 1945 CE",
                "key_civilizations": ["industrial_nations", "colonial_empires", "emerging_nations"],
                "major_themes": ["industrialization", "nationalism", "imperialism", "world_wars"],
                "primary_sources": ["government_documents", "newspapers", "photographs", "personal_letters"],
                "historical_skills": ["complex_analysis", "multiple_causation", "historical_synthesis"]
            },
            "contemporary_history": {
                "time_range": "1945 - Present",
                "key_civilizations": ["global_nations", "international_organizations", "emerging_powers"],
                "major_themes": ["cold_war", "decolonization", "globalization", "technological_revolution"],
                "primary_sources": ["diplomatic_documents", "media_reports", "digital_records", "oral_histories"],
                "historical_skills": ["recent_history_analysis", "ongoing_assessment", "future_projection"]
            }
        }
        
        # Historical thinking skills and concepts
        self.historical_thinking = {
            "chronological_thinking": {
                "skills": ["sequence_events", "identify_patterns", "understand_causation"],
                "activities": ["timeline_construction", "periodization", "causal_chain_analysis"],
                "assessment": ["chronological_ordering", "period_identification", "time_relationships"]
            },
            "historical_analysis": {
                "skills": ["analyze_sources", "identify_perspective", "evaluate_evidence"],
                "activities": ["source_comparison", "bias_detection", "evidence_weighting"],
                "assessment": ["source_authenticity", "perspective_analysis", "evidence_evaluation"]
            },
            "historical_comparison": {
                "skills": ["compare_societies", "identify_similarities", "recognize_differences"],
                "activities": ["comparative_studies", "pattern_recognition", "case_studies"],
                "assessment": ["analogical_reasoning", "thematic_comparison", "cross_cultural_analysis"]
            },
            "historical_argumentation": {
                "skills": ["develop_thesis", "support_claims", "counter_arguments"],
                "activities": ["historical_essays", "debate_participation", "research_projects"],
                "assessment": ["thesis_quality", "evidence_use", "reasoning_logical"]
            }
        }
        
        # Historical methodology components
        self.historical_methodology = {
            "primary_sources": {
                "types": ["documents", "artifacts", "visual_materials", "oral_testimonies"],
                "evaluation": ["authenticity", "purpose", "audience", "perspective"],
                "limitations": ["bias", "incomplete_record", "interpretive_challenges"]
            },
            "secondary_sources": {
                "types": ["scholarly_articles", "historiographies", "reference_works", "syntheses"],
                "evaluation": ["scholarly_credentials", "methodology", "evidence_base", "peer_review"],
                "contributions": ["interpretation", "synthesis", "new_perspectives", "methodological_innovation"]
            },
            "historical_context": {
                "political": ["governance_systems", "power_structures", "international_relations"],
                "social": ["class_structures", "family_life", "social_mobility", "cultural_practices"],
                "economic": ["production_systems", "trade_networks", "wealth_distribution", "technological_change"],
                "cultural": ["religious_beliefs", "intellectual_movements", "artistic_expressions", "ideological_systems"]
            }
        }
    
    async def provide_tutoring(
        self, 
        student_id: str, 
        topic: str, 
        difficulty_level: str = "intermediate",
        learning_objectives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Provide comprehensive history tutoring for a specific topic.
        
        Args:
            student_id: ID of the student agent
            topic: Historical topic (e.g., "french_revolution", "cold_war", "ancient_egypt")
            difficulty_level: Student's current level (beginner, intermediate, advanced)
            learning_objectives: Specific learning objectives for the session
        
        Returns:
            Comprehensive historical tutoring session data
        """
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Get or create history expert agent
            expert_agent = await self._get_or_create_expert_agent()
            session = ExpertSession(
                id=session_id,
                expert_agent_id=expert_agent.id,
                student_agent_id=student_id,
                domain=self.domain,
                topic=topic,
                session_type="tutoring",
                status="active",
                started_at=datetime.now(timezone.utc)
            )
            
            self.db.add(session)
            self.db.commit()
            
            # Analyze student's historical background and needs
            background_analysis = await self._analyze_historical_background(student_id, topic)
            
            # Generate personalized teaching plan
            teaching_plan = await self.expert_engine.create_teaching_plan(
                expert_agent.id, student_id, topic, difficulty_level
            )
            
            # Create historical explanation with multiple perspectives
            concept_explanation = await self._generate_historical_explanation(
                topic, difficulty_level, background_analysis, teaching_plan
            )
            
            # Generate source analysis exercises
            source_exercises = await self._generate_source_analysis_exercises(
                topic, difficulty_level, background_analysis
            )
            
            # Create timeline construction activities
            timeline_activities = await self._create_timeline_activities(
                topic, difficulty_level, background_analysis
            )
            
            # Generate comparative historical studies
            comparative_studies = await self._create_comparative_studies(
                topic, difficulty_level, background_analysis
            )
            
            # Create historical thinking skill exercises
            thinking_exercises = await self._create_historical_thinking_exercises(
                topic, difficulty_level, background_analysis
            )
            
            # Prepare historical argumentation practice
            argumentation_practice = await self._prepare_historical_argumentation_practice(
                topic, difficulty_level
            )
            
            tutoring_session = {
                "session_id": session_id,
                "expert_id": expert_agent.id,
                "student_id": student_id,
                "domain": self.domain,
                "topic": topic,
                "difficulty_level": difficulty_level,
                "learning_objectives": learning_objectives or await self._get_topic_objectives(topic),
                "background_analysis": background_analysis,
                "teaching_plan": teaching_plan,
                "concept_explanation": concept_explanation,
                "source_analysis_exercises": source_exercises,
                "timeline_activities": timeline_activities,
                "comparative_studies": comparative_studies,
                "historical_thinking_exercises": thinking_exercises,
                "argumentation_practice": argumentation_practice,
                "historical_methodology_integration": await self._integrate_historical_methodology(topic),
                "assessment_criteria": await self._define_historical_assessment_criteria(topic),
                "next_steps": await self._suggest_historical_next_steps(topic, difficulty_level),
                "created_at": datetime.now(timezone.utc)
            }
            
            # Update session with historical methods used
            session.methods_used = [
                "source_analysis", "multiple_perspectives", "chronological_thinking",
                "comparative_analysis", "historical_reasoning", "contextual_understanding"
            ]
            session.student_outcomes = {"historical_session_prepared": True}
            session.learning_objectives = tutoring_session["learning_objectives"]
            
            self.db.commit()
            
            logger.info(f"Created history tutoring session {session_id} for topic {topic}")
            return tutoring_session
            
        except Exception as e:
            logger.error(f"Error providing history tutoring: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_historical_sources(
        self, 
        source_materials: List[Dict[str, Any]],
        analysis_focus: str = "comprehensive",
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze historical sources with detailed evaluation and interpretation.
        
        Args:
            source_materials: List of historical sources (documents, artifacts, images, etc.)
            analysis_focus: Type of analysis (authenticity, perspective, bias, content, methodology)
            student_id: Optional student ID for educational context
        
        Returns:
            Comprehensive source analysis with historical context and interpretation
        """
        try:
            # Analyze each source individually
            individual_analyses = []
            for i, source in enumerate(source_materials):
                analysis = await self._analyze_individual_source(source, i)
                individual_analyses.append(analysis)
            
            # Conduct comparative analysis
            comparative_analysis = await self._conduct_comparative_source_analysis(
                individual_analyses, analysis_focus
            )
            
            # Evaluate source reliability and limitations
            reliability_assessment = await self._assess_source_reliability(individual_analyses)
            
            # Identify potential biases and perspectives
            bias_analysis = await self._identify_source_biases(individual_analyses)
            
            # Extract historical information and themes
            content_analysis = await self._extract_historical_content(individual_analyses)
            
            # Provide historical context
            contextual_analysis = await self._provide_historical_context(source_materials)
            
            # Generate critical thinking questions
            critical_questions = await self._generate_critical_source_questions(
                individual_analyses, analysis_focus
            )
            
            # Create source synthesis
            synthesis = await self._create_source_synthesis(
                individual_analyses, comparative_analysis, content_analysis
            )
            
            # Provide historical interpretation
            interpretation = await self._provide_historical_interpretation(
                synthesis, source_materials, analysis_focus
            )
            
            # Generate educational guidance if student_id provided
            educational_guidance = {}
            if student_id:
                educational_guidance = await self._create_educational_source_guidance(
                    individual_analyses, student_id, analysis_focus
                )
            
            source_analysis = {
                "analysis_id": str(uuid.uuid4()),
                "analysis_focus": analysis_focus,
                "source_count": len(source_materials),
                "individual_analyses": individual_analyses,
                "comparative_analysis": comparative_analysis,
                "reliability_assessment": reliability_assessment,
                "bias_analysis": bias_analysis,
                "content_analysis": content_analysis,
                "contextual_analysis": contextual_analysis,
                "critical_questions": critical_questions,
                "source_synthesis": synthesis,
                "historical_interpretation": interpretation,
                "educational_guidance": educational_guidance,
                "research_recommendations": await self._generate_source_research_recommendations(source_materials),
                "created_at": datetime.now(timezone.utc)
            }
            
            return source_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing historical sources: {str(e)}")
            return {"error": str(e)}
    
    async def construct_historical_timeline(
        self, 
        historical_topic: str,
        time_range: Optional[Tuple[str, str]] = None,
        student_id: Optional[str] = None,
        complexity_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Construct comprehensive historical timelines with multiple perspectives and context.
        
        Args:
            historical_topic: Historical period or event to timeline
            time_range: Optional tuple of (start_date, end_date)
            student_id: Optional student ID for personalization
            complexity_level: Complexity level of timeline construction
        
        Returns:
            Detailed historical timeline with events, context, and analysis
        """
        try:
            # Determine appropriate time range if not specified
            determined_range = time_range or await self._determine_time_range(historical_topic)
            
            # Identify key events and developments
            key_events = await self._identify_key_historical_events(historical_topic, determined_range)
            
            # Research background context for each period
            period_contexts = await self._research_period_contexts(historical_topic, determined_range)
            
            # Create chronological sequence
            chronological_sequence = await self._create_chronological_sequence(
                key_events, period_contexts
            )
            
            # Identify cause-and-effect relationships
            causal_relationships = await self._identify_causal_relationships(chronological_sequence)
            
            # Add multiple perspectives and interpretations
            multiple_perspectives = await self._add_multiple_historical_perspectives(
                chronological_sequence, historical_topic
            )
            
            # Include turning points and pivotal moments
            turning_points = await self._identify_historical_turning_points(chronological_sequence)
            
            # Create thematic connections
            thematic_connections = await self._create_thematic_timeline_connections(
                chronological_sequence, historical_topic
            )
            
            # Add historical figures and their roles
            historical_figures = await self._research_historical_figures(
                chronological_sequence, historical_topic
            )
            
            # Include technological and cultural developments
            developments = await self._identify_key_developments(
                chronological_sequence, historical_topic
            )
            
            # Create visual representation suggestions
            visual_suggestions = await self._suggest_timeline_visualizations(
                chronological_sequence, complexity_level
            )
            
            # Provide analysis and interpretation guidance
            analysis_guidance = await self._provide_timeline_analysis_guidance(
                chronological_sequence, historical_topic
            )
            
            # Generate discussion questions
            discussion_questions = await self._generate_timeline_discussion_questions(
                chronological_sequence, historical_topic
            )
            
            # Create assessment opportunities
            assessment_opportunities = await self._create_timeline_assessment_opportunities(
                chronological_sequence, complexity_level
            )
            
            # Provide educational adaptations if student_id available
            educational_adaptations = {}
            if student_id:
                educational_adaptations = await self._create_timeline_educational_adaptations(
                    student_id, historical_topic, complexity_level
                )
            
            timeline_construction = {
                "timeline_id": str(uuid.uuid4()),
                "historical_topic": historical_topic,
                "time_range": determined_range,
                "complexity_level": complexity_level,
                "chronological_sequence": chronological_sequence,
                "causal_relationships": causal_relationships,
                "multiple_perspectives": multiple_perspectives,
                "turning_points": turning_points,
                "thematic_connections": thematic_connections,
                "historical_figures": historical_figures,
                "key_developments": developments,
                "visual_representation": visual_suggestions,
                "analysis_guidance": analysis_guidance,
                "discussion_questions": discussion_questions,
                "assessment_opportunities": assessment_opportunities,
                "educational_adaptations": educational_adaptations,
                "created_at": datetime.now(timezone.utc)
            }
            
            return timeline_construction
            
        except Exception as e:
            logger.error(f"Error constructing historical timeline: {str(e)}")
            return {"error": str(e)}
    
    async def facilitate_historical_comparison(
        self, 
        comparison_subjects: List[str],
        comparison_focus: str = "comprehensive",
        historical_periods: Optional[List[str]] = None,
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Facilitate comparative historical analysis across different societies, periods, or themes.
        
        Args:
            comparison_subjects: List of societies, events, or phenomena to compare
            comparison_focus: Type of comparison (political, social, economic, cultural, thematic)
            historical_periods: Optional list of specific time periods to focus on
            student_id: Optional student ID for educational context
        
        Returns:
            Comprehensive comparative historical analysis framework
        """
        try:
            # Analyze each subject for comparison
            subject_analyses = []
            for subject in comparison_subjects:
                analysis = await self._analyze_comparison_subject(subject, comparison_focus)
                subject_analyses.append(analysis)
            
            # Identify comparison criteria and dimensions
            comparison_criteria = await self._identify_comparison_criteria(
                comparison_subjects, comparison_focus
            )
            
            # Create comparison framework
            comparison_framework = await self._create_comparison_framework(
                subject_analyses, comparison_criteria
            )
            
            # Conduct systematic comparison
            systematic_comparison = await self._conduct_systematic_comparison(
                subject_analyses, comparison_criteria, comparison_framework
            )
            
            # Identify similarities and differences
            similarities_differences = await self._identify_similarities_differences(
                systematic_comparison
            )
            
            # Analyze patterns and trends
            pattern_analysis = await self._analyze_historical_patterns(
                systematic_comparison, comparison_focus
            )
            
            # Explore causal relationships
            causal_analysis = await self._explore_causal_relationships(
                similarities_differences, comparison_subjects
            )
            
            # Consider multiple perspectives
            perspective_analysis = await self._consider_multiple_historical_perspectives(
                comparison_subjects, comparison_focus
            )
            
            # Evaluate significance and impact
            significance_evaluation = await self._evaluate_historical_significance(
                similarities_differences, comparison_subjects
            )
            
            # Create comparative timeline
            comparative_timeline = await self._create_comparative_timeline(
                subject_analyses, historical_periods
            )
            
            # Generate analytical conclusions
            analytical_conclusions = await self._generate_analytical_conclusions(
                systematic_comparison, pattern_analysis, causal_analysis
            )
            
            # Provide research recommendations
            research_recommendations = await self._generate_comparative_research_recommendations(
                comparison_subjects, comparison_focus
            )
            
            # Create discussion framework
            discussion_framework = await self._create_comparative_discussion_framework(
                systematic_comparison, comparison_focus
            )
            
            # Provide educational adaptations if student_id available
            educational_adaptations = {}
            if student_id:
                educational_adaptations = await self._create_comparative_educational_adaptations(
                    student_id, comparison_subjects, comparison_focus
                )
            
            historical_comparison = {
                "comparison_id": str(uuid.uuid4()),
                "comparison_subjects": comparison_subjects,
                "comparison_focus": comparison_focus,
                "historical_periods": historical_periods,
                "subject_analyses": subject_analyses,
                "comparison_criteria": comparison_criteria,
                "comparison_framework": comparison_framework,
                "systematic_comparison": systematic_comparison,
                "similarities_differences": similarities_differences,
                "pattern_analysis": pattern_analysis,
                "causal_analysis": causal_analysis,
                "perspective_analysis": perspective_analysis,
                "significance_evaluation": significance_evaluation,
                "comparative_timeline": comparative_timeline,
                "analytical_conclusions": analytical_conclusions,
                "research_recommendations": research_recommendations,
                "discussion_framework": discussion_framework,
                "educational_adaptations": educational_adaptations,
                "created_at": datetime.now(timezone.utc)
            }
            
            return historical_comparison
            
        except Exception as e:
            logger.error(f"Error facilitating historical comparison: {str(e)}")
            return {"error": str(e)}
    
    async def guide_historical_research(
        self, 
        research_question: str,
        student_id: Optional[str] = None,
        research_stage: str = "question_formation"
    ) -> Dict[str, Any]:
        """
        Guide students through the historical research process from question formation to conclusion.
        
        Args:
            research_question: Historical research question to investigate
            student_id: Optional student ID for personalized guidance
            research_stage: Current stage of research process
        
        Returns:
            Comprehensive historical research guidance and methodology
        """
        try:
            # Analyze research question for historical components
            question_analysis = await self._analyze_historical_research_question(research_question)
            
            # Assess research question quality and feasibility
            quality_assessment = await self._assess_question_quality(research_question, question_analysis)
            
            # Provide stage-specific guidance
            stage_guidance = await self._provide_stage_specific_guidance(
                research_stage, research_question, quality_assessment
            )
            
            # Create research plan
            research_plan = await self._create_historical_research_plan(
                research_question, question_analysis, research_stage
            )
            
            # Suggest appropriate source types
            source_recommendations = await self._recommend_appropriate_sources(
                research_question, question_analysis
            )
            
            # Provide source evaluation criteria
            evaluation_criteria = await self._provide_source_evaluation_criteria(
                question_analysis, research_stage
            )
            
            # Guide evidence gathering
            evidence_guidance = await self._guide_evidence_gathering(
                research_question, source_recommendations
            )
            
            # Support analysis and synthesis
            analysis_guidance = await self._provide_analysis_guidance(
                research_question, research_stage
            )
            
            # Help with argument development
            argumentation_guidance = await self._provide_argumentation_guidance(
                research_question, research_stage
            )
            
            # Provide writing and presentation support
            communication_guidance = await self._provide_communication_guidance(
                research_question, research_stage
            )
            
            # Create progress tracking tools
            progress_tracking = await self._create_research_progress_tracking(
                research_stage, research_plan
            )
            
            # Provide peer collaboration opportunities
            collaboration_opportunities = await self._suggest_collaboration_opportunities(
                research_question, research_stage
            )
            
            # Generate assessment criteria
            assessment_criteria = await self._define_research_assessment_criteria(
                research_question, research_stage
            )
            
            # Provide educational adaptations if student_id available
            educational_adaptations = {}
            if student_id:
                educational_adaptations = await self._create_research_educational_adaptations(
                    student_id, research_question, research_stage
                )
            
            research_guidance = {
                "guidance_id": str(uuid.uuid4()),
                "research_question": research_question,
                "research_stage": research_stage,
                "question_analysis": question_analysis,
                "quality_assessment": quality_assessment,
                "stage_guidance": stage_guidance,
                "research_plan": research_plan,
                "source_recommendations": source_recommendations,
                "evaluation_criteria": evaluation_criteria,
                "evidence_guidance": evidence_guidance,
                "analysis_guidance": analysis_guidance,
                "argumentation_guidance": argumentation_guidance,
                "communication_guidance": communication_guidance,
                "progress_tracking": progress_tracking,
                "collaboration_opportunities": collaboration_opportunities,
                "assessment_criteria": assessment_criteria,
                "educational_adaptations": educational_adaptations,
                "created_at": datetime.now(timezone.utc)
            }
            
            return research_guidance
            
        except Exception as e:
            logger.error(f"Error guiding historical research: {str(e)}")
            return {"error": str(e)}
    
    # ==================== Private Helper Methods ====================
    
    async def _get_or_create_expert_agent(self) -> UniversityAgent:
        """Get or create history expert agent"""
        # Look for existing history expert
        expert_profiles = self.db.query(DomainExpertProfile).filter(
            DomainExpertProfile.domain_name == self.domain
        ).all()
        
        if expert_profiles:
            # Return the most successful expert
            best_expert = max(
                expert_profiles, 
                key=lambda x: x.success_rate
            )
            agent = self.db.query(UniversityAgent).filter(
                UniversityAgent.id == best_expert.agent_id
            ).first()
            return agent
        
        # Create new history expert
        agent_id = str(uuid.uuid4())
        agent = UniversityAgent(
            id=agent_id,
            university_id=str(uuid.uuid4()),
            name="Professor History",
            agent_type="expert",
            specialization="history",
            status="active",
            competency_score=1.0
        )
        
        expert_profile = DomainExpertProfile(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            domain_name=self.domain,
            expertise_level="expert",
            teaching_style="analytical",
            success_rate=0.85,
            available_capabilities=[
                "historical_analysis", "source_evaluation", "chronological_thinking",
                "comparative_history", "historical_research", "critical_thinking",
                "historical_reasoning", "primary_source_analysis", "historical_synthesis",
                "multiple_perspectives", "causal_analysis", "historical_argumentation"
            ]
        )
        
        self.db.add(agent)
        self.db.add(expert_profile)
        self.db.commit()
        
        return agent
    
    async def _analyze_historical_background(
        self, student_id: str, topic: str
    ) -> Dict[str, Any]:
        """Analyze student's historical background and learning needs"""
        # Get student's learning profile for history
        learning_profile = self.db.query(StudentLearningProfile).filter(
            and_(
                StudentLearningProfile.agent_id == student_id,
                StudentLearningProfile.domain == self.domain
            )
        ).first()
        
        # Get past history sessions and performance
        past_sessions = self.db.query(ExpertSession).filter(
            and_(
                ExpertSession.student_agent_id == student_id,
                ExpertSession.domain == self.domain
            )
        ).order_by(desc(ExpertSession.created_at)).limit(10).all()
        
        background_analysis = {
            "student_id": student_id,
            "topic": topic,
            "learning_style": learning_profile.learning_style if learning_profile else "reading",
            "historical_knowledge": await self._assess_historical_knowledge(past_sessions),
            "source_analysis_skills": await self._assess_source_analysis_skills(past_sessions),
            "chronological_thinking": await self._assess_chronological_thinking(past_sessions),
            "critical_thinking_level": await self._assess_critical_thinking_level(past_sessions),
            "research_skills": await self._assess_research_skills(past_sessions),
            "preferred_historical_periods": await self._identify_preferred_periods(past_sessions),
            "writing_proficiency": await self._assess_historical_writing_proficiency(past_sessions),
            "areas_of_interest": await self._identify_historical_interests(past_sessions)
        }
        
        return background_analysis
    
    async def _generate_historical_explanation(
        self, 
        topic: str, 
        difficulty_level: str,
        background_analysis: Dict[str, Any],
        teaching_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive historical explanation with multiple perspectives"""
        # Get knowledge node for the topic
        knowledge_node = self.db.query(KnowledgeNode).filter(
            and_(
                KnowledgeNode.domain == self.domain,
                KnowledgeNode.topic == topic,
                KnowledgeNode.difficulty_level == difficulty_level
            )
        ).first()
        
        if knowledge_node:
            explanation_data = {
                "concept_name": knowledge_node.concept_name,
                "historical_explanation": knowledge_node.concept_data.get("explanation", ""),
                "key_events": knowledge_node.concept_data.get("events", []),
                "historical_context": knowledge_node.concept_data.get("context", []),
                "multiple_perspectives": knowledge_node.concept_data.get("perspectives", []),
                "primary_sources": knowledge_node.examples or [],
                "historical_significance": knowledge_node.real_world_applications or [],
                "misconceptions": knowledge_node.common_misconceptions or []
            }
        else:
            # Generate explanation based on historical period
            explanation_data = await self._generate_fallback_historical_explanation(topic, difficulty_level)
        
        # Add historical methodology integration
        explanation_data["methodology_elements"] = await self._integrate_historical_methodology_elements(
            explanation_data, topic
        )
        
        return explanation_data
    
    # Placeholder implementations for remaining methods
    async def _get_topic_objectives(self, topic: str) -> List[str]:
        # 1. Try to fetch from Knowledge Base
        node = self.db.query(KnowledgeNode).filter(
            and_(
                KnowledgeNode.domain == self.domain,
                KnowledgeNode.topic == topic
            )
        ).first()
        
        if node and node.learning_objectives:
            return node.learning_objectives

        # 2. Fallback
        return ["understand_historical_context", "analyze_primary_sources", "evaluate_historical_significance"]
    
    async def _define_historical_assessment_criteria(self, topic: str) -> Dict[str, Any]:
        # 1. Try to fetch from Knowledge Base
        node = self.db.query(KnowledgeNode).filter(
            and_(
                KnowledgeNode.domain == self.domain,
                KnowledgeNode.topic == topic
            )
        ).first()
        
        if node and node.assessment_criteria:
            # Convert list to weighted dict if necessary
            criteria_list = node.assessment_criteria
            if isinstance(criteria_list, list) and criteria_list:
                weight = 1.0 / len(criteria_list)
                return {c: weight for c in criteria_list}
            elif isinstance(criteria_list, dict):
                return criteria_list

        # 2. Fallback
        return {
            "historical_accuracy": 0.3,
            "argument_quality": 0.3,
            "evidence_usage": 0.2,
            "contextual_understanding": 0.2
        }
    
    async def _suggest_historical_next_steps(self, topic: str, difficulty_level: str) -> List[str]:
        next_steps = []
        
        # 1. Check Knowledge Base
        node = self.db.query(KnowledgeNode).filter(
            and_(KnowledgeNode.domain == self.domain, KnowledgeNode.topic == topic)
        ).first()
        
        if node and node.connections:
            if isinstance(node.connections, list):
                 next_steps.extend([f"Explore {conn}" for conn in node.connections[:2]])

        # 2. Check Historical Periods
        found = False
        # Assuming self.historical_periods is defined elsewhere, e.g., in __init__
        # For this example, I'll define a dummy one to make the code syntactically valid
        if not hasattr(self, 'historical_periods'):
            self.historical_periods = {
                "ancient_history": {"key_civilizations": ["Egypt", "Rome"], "major_themes": ["empires"]},
                "medieval_history": {"key_civilizations": ["Byzantium"], "major_themes": ["feudalism"]},
                "early_modern_history": {"key_civilizations": ["Ottoman Empire"], "major_themes": ["renaissance"]}
            }
        
        periods = list(self.historical_periods.keys())
        for i, period_key in enumerate(periods):
            info = self.historical_periods[period_key]
            # Check if topic is in key civilizations or major themes, or is the period itself
            if topic == period_key or \
               ("key_civilizations" in info and topic in info["key_civilizations"]) or \
               ("major_themes" in info and topic in info["major_themes"]):
                if i < len(periods) - 1:
                    next_steps.append(f"Advance to {periods[i+1].replace('_', ' ').title()}")
                    found = True
                break
        
        if not next_steps:
             next_steps = [f"Deepen analysis of {topic}", "Comparative historical study"]
             
        return next_steps
    
    async def _integrate_historical_methodology(self, topic: str) -> Dict[str, Any]:
        return {
            "primary_sources": True,
            "secondary_sources": True,
            "multiple_perspectives": True,
            "historical_context": True
        }
    
    # Additional placeholder implementations would continue here...
    async def _analyze_historical_background(self, student_id: str, topic: str) -> Dict[str, Any]:
        return {"historical_background": "analyzed"}
    
    async def _generate_fallback_historical_explanation(self, topic: str, difficulty_level: str) -> Dict[str, Any]:
        return {
            "concept_name": topic,
            "historical_explanation": f"Understanding {topic} requires careful analysis of historical context.",
            "key_events": ["event_1", "event_2"],
            "historical_context": ["context_1", "context_2"],
            "multiple_perspectives": ["perspective_1", "perspective_2"],
            "primary_sources": [],
            "historical_significance": [],
            "misconceptions": []
        }
    
    async def _integrate_historical_methodology_elements(self, explanation_data: Dict[str, Any], topic: str) -> Dict[str, Any]:
        return {"methodology_integration": "comprehensive", "source_analysis": "included"}
    
    async def _assess_historical_knowledge(self, sessions: List) -> Dict[str, Any]:
        return {"period_familiarity": "good", "fact_accuracy": "high", "concept_understanding": "developing"}
    
    async def _assess_source_analysis_skills(self, sessions: List) -> Dict[str, Any]:
        return {"evaluation_ability": "intermediate", "bias_detection": "emerging", "context_understanding": "good"}
    
    async def _assess_chronological_thinking(self, sessions: List) -> Dict[str, Any]:
        return {"sequence_understanding": "good", "causal_reasoning": "developing", "time_relationships": "intermediate"}
    
    async def _assess_critical_thinking_level(self, sessions: List) -> str:
        return "developing"
    
    async def _assess_research_skills(self, sessions: List) -> Dict[str, Any]:
        return {"source_gathering": "basic", "evidence_evaluation": "intermediate", "synthesis_ability": "emerging"}
    
    async def _identify_preferred_periods(self, sessions: List) -> List[str]:
        return ["modern_history", "contemporary_history"]
    
    async def _assess_historical_writing_proficiency(self, sessions: List) -> Dict[str, Any]:
        return {"argumentation": "developing", "evidence_use": "good", "historical_language": "appropriate"}
    
    async def _identify_historical_interests(self, sessions: List) -> List[str]:
        return ["political_history", "social_history", "cultural_history"]
    
    # Exercise generation methods would continue here...
    async def _generate_source_analysis_exercises(self, topic: str, difficulty_level: str, background_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _create_timeline_activities(self, topic: str, difficulty_level: str, background_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _create_comparative_studies(self, topic: str, difficulty_level: str, background_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _create_historical_thinking_exercises(self, topic: str, difficulty_level: str, background_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _prepare_historical_argumentation_practice(self, topic: str, difficulty_level: str) -> Dict[str, Any]:
        return {"argument_types": ["cause_effect", "comparison", "continuity_change"]}
    
    # Many more methods would be implemented for the complete system...
    # This provides the core structure and key functionality