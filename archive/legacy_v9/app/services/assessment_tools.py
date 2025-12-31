"""
Assessment and Evaluation Tools Engine

Comprehensive assessment creation, evaluation, and analytics capabilities.
Part of DRYAD.AI Armory System for comprehensive educational assessment tools.
"""

import logging
import asyncio
import json
import uuid
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import numpy as np
from collections import defaultdict

from .content_creation import ToolCategory, ToolSecurityLevel

logger = logging.getLogger(__name__)


class AssessmentType(str, Enum):
    """Types of assessments"""
    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    PORTFOLIO = "portfolio"
    PRESENTATION = "presentation"
    PRACTICAL = "practical"
    PEER_REVIEW = "peer_review"
    SELF_ASSESSMENT = "self_assessment"
    SKILLS_ASSESSMENT = "skills_assessment"


class QuestionType(str, Enum):
    """Types of assessment questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    DRAG_DROP = "drag_drop"
    CODING = "coding"
    CALCULATION = "calculation"
    CASE_STUDY = "case_study"


class EvaluationMethod(str, Enum):
    """Methods for evaluation"""
    AUTOMATED_GRADING = "automated_grading"
    RUBRIC_BASED = "rubric_based"
    PEER_ASSESSMENT = "peer_assessment"
    INSTRUCTOR_REVIEW = "instructor_review"
    AI_ASSISTED = "ai_assisted"
    HYBRID = "hybrid"


class DifficultyLevel(str, Enum):
    """Assessment difficulty levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class GradingScale(str, Enum):
    """Grading scales"""
    PERCENTAGE = "percentage"
    LETTER_GRADES = "letter_grades"
    NUMERIC = "numeric"
    PASS_FAIL = "pass_fail"
    RUBRIC_SCORE = "rubric_score"


@dataclass
class AssessmentSpec:
    """Assessment specification"""
    spec_id: str
    assessment_type: AssessmentType
    title: str
    description: str
    subject_area: str
    target_audience: str  # undergraduate, graduate, professional
    difficulty_level: DifficultyLevel
    time_limit_minutes: int = 60
    max_attempts: int = 3
    questions: List[Dict[str, Any]] = field(default_factory=list)
    evaluation_method: EvaluationMethod = EvaluationMethod.AUTOMATED_GRADING
    grading_scale: GradingScale = GradingScale.PERCENTAGE
    passing_score: float = 70.0
    randomize_questions: bool = False
    immediate_feedback: bool = True
    show_correct_answers: bool = True
    
    def __post_init__(self):
        if not self.spec_id:
            self.spec_id = f"assessment_spec_{uuid.uuid4().hex[:8]}"


@dataclass
class Question:
    """Individual assessment question"""
    question_id: str
    question_text: str
    question_type: QuestionType
    difficulty_level: DifficultyLevel
    points: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.question_id:
            self.question_id = f"q_{uuid.uuid4().hex[:8]}"


@dataclass
class AnswerOption:
    """Answer option for multiple choice questions"""
    option_id: str
    option_text: str
    is_correct: bool = False
    explanation: str = ""
    points: float = 0.0
    
    def __post_init__(self):
        if not self.option_id:
            self.option_id = f"opt_{uuid.uuid4().hex[:8]}"


@dataclass
class RubricCriterion:
    """Rubric criterion for evaluation"""
    criterion_id: str
    name: str
    description: str
    max_points: float
    performance_levels: List[Dict[str, Any]] = field(default_factory=list)
    weight: float = 1.0
    
    def __post_init__(self):
        if not self.criterion_id:
            self.criterion_id = f"rubric_{uuid.uuid4().hex[:8]}"


@dataclass
class AssessmentResult:
    """Result of assessment completion"""
    result_id: str
    assessment_id: str
    student_id: str
    total_score: float
    max_score: float
    percentage_score: float
    grade: str
    time_spent_minutes: int
    answers: List[Dict[str, Any]] = field(default_factory=list)
    feedback: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.result_id:
            self.result_id = f"result_{uuid.uuid4().hex[:8]}"


@dataclass
class StudentPerformance:
    """Student performance analytics"""
    student_id: str
    assessment_results: List[AssessmentResult] = field(default_factory=list)
    skill_progression: Dict[str, float] = field(default_factory=dict)
    areas_of_strength: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    overall_performance_score: float = 0.0


@dataclass
class AssessmentAnalytics:
    """Assessment analytics data"""
    assessment_id: str
    total_participants: int
    completion_rate: float
    average_score: float
    score_distribution: Dict[str, int]
    difficulty_analysis: Dict[str, float]
    item_analysis: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class AssessmentCreationEngine:
    """Engine for creating comprehensive assessments"""
    
    def __init__(self, db_session=None):
        self.assessment_templates = self._load_assessment_templates()
        self.evaluation_engine = EvaluationEngine()
        self.analytics_engine = AssessmentAnalyticsEngine()
        self.rubric_generator = RubricGenerator()
        
        # Assessment management
        self.created_assessments: Dict[str, AssessmentSpec] = {}
        self.assessment_results: Dict[str, List[AssessmentResult]] = {}
        
        # Initialize assessment tools
        asyncio.create_task(self._initialize_assessment_tools())
    
    async def _initialize_assessment_tools(self):
        """Initialize assessment tools in the tool registry"""
        assessment_tools = [
            {
                "name": "Quiz Generator",
                "description": "AI-powered quiz and assessment creation",
                "category": ToolCategory.CONTENT_CREATION,
                "schema_json": {
                    "openapi": "3.0.0",
                    "info": {"title": "Quiz Generator", "version": "1.0.0"},
                    "paths": {
                        "/create_quiz": {
                            "post": {
                                "summary": "Generate quiz questions",
                                "parameters": [
                                    {"name": "topic", "in": "query", "schema": {"type": "string"}},
                                    {"name": "num_questions", "in": "query", "schema": {"type": "integer"}}
                                ]
                            }
                        }
                    }
                }
            },
            {
                "name": "Rubric Builder",
                "description": "Create detailed evaluation rubrics",
                "category": ToolCategory.CONTENT_CREATION,
                "schema_json": {
                    "openapi": "3.0.0",
                    "info": {"title": "Rubric Builder", "version": "1.0.0"},
                    "paths": {
                        "/create_rubric": {
                            "post": {
                                "summary": "Create evaluation rubric",
                                "parameters": [
                                    {"name": "assessment_type", "in": "query", "schema": {"type": "string"}},
                                    {"name": "criteria", "in": "query", "schema": {"type": "array"}}
                                ]
                            }
                        }
                    }
                }
            }
        ]
        
        # Note: In a real implementation, these would be registered with the tool registry
        logger.info("Assessment creation tools initialized")
    
    def _load_assessment_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load assessment templates for different types"""
        return {
            "quiz": {
                "structure": ["introduction", "questions", "submission"],
                "question_types": [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.SHORT_ANSWER],
                "time_limit": 30,
                "max_attempts": 3,
                "passing_score": 70
            },
            "exam": {
                "structure": ["instructions", "sections", "questions", "review", "submission"],
                "question_types": [QuestionType.ESSAY, QuestionType.MULTIPLE_CHOICE, QuestionType.CALCULATION],
                "time_limit": 120,
                "max_attempts": 1,
                "passing_score": 65
            },
            "assignment": {
                "structure": ["overview", "requirements", "rubric", "submission_guidelines"],
                "evaluation_method": EvaluationMethod.RUBRIC_BASED,
                "time_limit": 1440,  # 24 hours
                "max_attempts": 1,
                "passing_score": 70
            },
            "project": {
                "structure": ["project_overview", "milestones", "deliverables", "evaluation_criteria"],
                "evaluation_method": EvaluationMethod.PEER_ASSESSMENT,
                "time_limit": 10080,  # 7 days
                "max_attempts": 1,
                "passing_score": 75
            }
        }
    
    async def create_assessment(self, assessment_spec: AssessmentSpec) -> Dict[str, Any]:
        """Create a comprehensive assessment"""
        try:
            logger.info(f"Creating assessment: {assessment_spec.title}")
            
            start_time = datetime.utcnow()
            
            # Generate questions if not provided
            if not assessment_spec.questions:
                questions = await self._generate_assessment_questions(assessment_spec)
                assessment_spec.questions = questions
            
            # Create assessment structure
            assessment_structure = await self._create_assessment_structure(assessment_spec)
            
            # Generate rubric if needed
            rubric = None
            if assessment_spec.evaluation_method in [EvaluationMethod.RUBRIC_BASED, EvaluationMethod.HYBRID]:
                rubric = await self.rubric_generator.create_rubric(assessment_spec)
            
            # Validate assessment
            validation_result = await self._validate_assessment(assessment_spec)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "assessment": assessment_spec,
                "assessment_structure": assessment_structure,
                "rubric": rubric,
                "validation_result": validation_result,
                "creation_time_ms": int(execution_time),
                "creation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Assessment creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "assessment_spec": assessment_spec.__dict__ if hasattr(assessment_spec, '__dict__') else {}
            }
    
    async def create_quick_assessment(self, topic: str, question_count: int = 10) -> Dict[str, Any]:
        """Create a quick assessment on a specific topic"""
        try:
            logger.info(f"Creating quick assessment on: {topic}")
            
            # Create basic assessment spec
            assessment_spec = AssessmentSpec(
                assessment_type=AssessmentType.QUIZ,
                title=f"Quick Assessment: {topic}",
                description=f"Quick assessment covering key concepts in {topic}",
                subject_area="General",
                target_audience="General",
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                time_limit_minutes=30,
                max_attempts=3,
                num_questions=question_count
            )
            
            # Generate questions
            questions = await self._generate_quick_questions(topic, question_count)
            assessment_spec.questions = questions
            
            return await self.create_assessment(assessment_spec)
            
        except Exception as e:
            logger.error(f"Quick assessment creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "topic": topic
            }
    
    async def build_rubric_for_assessment(self, assessment_spec: AssessmentSpec) -> Dict[str, Any]:
        """Build comprehensive rubric for assessment"""
        try:
            logger.info(f"Building rubric for: {assessment_spec.title}")
            
            rubric = await self.rubric_generator.create_rubric(assessment_spec)
            
            return {
                "success": True,
                "rubric": rubric,
                "assessment_id": assessment_spec.spec_id,
                "rubric_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rubric building failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "assessment_spec": assessment_spec.__dict__ if hasattr(assessment_spec, '__dict__') else {}
            }
    
    async def generate_question_bank(self, topic: str, question_types: List[QuestionType], difficulty_levels: List[DifficultyLevel]) -> List[Question]:
        """Generate a bank of questions on a specific topic"""
        try:
            logger.info(f"Generating question bank for: {topic}")
            
            question_bank = []
            
            for question_type in question_types:
                for difficulty in difficulty_levels:
                    # Generate questions for each type and difficulty combination
                    questions = await self._generate_question_set(topic, question_type, difficulty)
                    question_bank.extend(questions)
            
            return question_bank
            
        except Exception as e:
            logger.error(f"Question bank generation failed: {e}")
            return []
    
    async def assess_question_quality(self, question: Question, learning_objectives: List[str]) -> Dict[str, Any]:
        """Assess the quality of individual questions"""
        try:
            logger.info(f"Assessing question quality: {question.question_id}")
            
            # Analyze question complexity
            complexity_analysis = await self._analyze_question_complexity(question)
            
            # Check alignment with learning objectives
            alignment_score = await self._assess_learning_objective_alignment(question, learning_objectives)
            
            # Evaluate clarity and readability
            clarity_score = await self._assess_question_clarity(question)
            
            # Calculate overall quality score
            quality_score = (complexity_analysis["complexity_score"] * 0.3 + 
                           alignment_score * 0.4 + 
                           clarity_score * 0.3)
            
            # Generate improvement suggestions
            suggestions = await self._generate_question_improvement_suggestions(
                question, complexity_analysis, alignment_score, clarity_score
            )
            
            return {
                "success": True,
                "question_id": question.question_id,
                "quality_score": quality_score,
                "complexity_analysis": complexity_analysis,
                "alignment_score": alignment_score,
                "clarity_score": clarity_score,
                "improvement_suggestions": suggestions,
                "assessment_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Question quality assessment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": question.__dict__ if hasattr(question, '__dict__') else {}
            }
    
    async def _generate_assessment_questions(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Generate questions for assessment based on spec"""
        questions = []
        
        # Template for different assessment types
        templates = {
            AssessmentType.QUIZ: self._generate_quiz_questions,
            AssessmentType.EXAM: self._generate_exam_questions,
            AssessmentType.ASSIGNMENT: self._generate_assignment_questions,
            AssessmentType.PROJECT: self._generate_project_questions
        }
        
        generator_func = templates.get(assessment_spec.assessment_type, self._generate_generic_questions)
        
        questions = await generator_func(assessment_spec)
        
        return questions
    
    async def _generate_quiz_questions(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Generate quiz questions"""
        questions = []
        
        # Generate different types of questions
        mc_questions = await self._generate_multiple_choice_questions(assessment_spec, 5)
        tf_questions = await self._generate_true_false_questions(assessment_spec, 3)
        short_questions = await self._generate_short_answer_questions(assessment_spec, 2)
        
        questions.extend(mc_questions)
        questions.extend(tf_questions)
        questions.extend(short_questions)
        
        return questions
    
    async def _generate_exam_questions(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Generate exam questions"""
        questions = []
        
        # Generate more complex questions for exams
        essay_questions = await self._generate_essay_questions(assessment_spec, 3)
        calculation_questions = await self._generate_calculation_questions(assessment_spec, 4)
        case_study_questions = await self._generate_case_study_questions(assessment_spec, 2)
        
        questions.extend(essay_questions)
        questions.extend(calculation_questions)
        questions.extend(case_study_questions)
        
        return questions
    
    async def _generate_assignment_questions(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Generate assignment questions"""
        questions = []
        
        # Generate project-based questions
        project_questions = await self._generate_project_questions(assessment_spec, 1)
        research_questions = await self._generate_research_questions(assessment_spec, 2)
        
        questions.extend(project_questions)
        questions.extend(research_questions)
        
        return questions
    
    async def _generate_project_questions(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Generate project questions"""
        questions = []
        
        # Simulate project question generation
        question_data = {
            "question_id": f"project_{uuid.uuid4().hex[:8]}",
            "question_text": f"Complete a comprehensive project on {assessment_spec.subject_area} demonstrating mastery of key concepts.",
            "question_type": QuestionType.CASE_STUDY,
            "difficulty_level": assessment_spec.difficulty_level,
            "points": 100.0,
            "rubric_criteria": [
                {"criterion": "Research Quality", "max_points": 25},
                {"criterion": "Analysis Depth", "max_points": 25},
                {"criterion": "Presentation", "max_points": 25},
                {"criterion": "Innovation", "max_points": 25}
            ],
            "instructions": [
                "Conduct thorough research on the topic",
                "Analyze findings using appropriate methodologies",
                "Present conclusions clearly and professionally",
                "Include creative insights and original thinking"
            ]
        }
        
        questions.append(question_data)
        return questions
    
    async def _generate_generic_questions(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Generate generic questions"""
        questions = []
        
        # Generate basic generic questions
        for i in range(5):
            question_data = {
                "question_id": f"generic_{uuid.uuid4().hex[:8]}",
                "question_text": f"Question {i+1}: Explain the key concepts related to {assessment_spec.subject_area}.",
                "question_type": QuestionType.SHORT_ANSWER,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 10.0,
                "sample_answer": f"Sample answer for question {i+1} about {assessment_spec.subject_area}"
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_multiple_choice_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate multiple choice questions"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question_id": f"mc_{uuid.uuid4().hex[:8]}",
                "question_text": f"Which of the following best describes a key concept in {assessment_spec.subject_area}?",
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 5.0,
                "options": [
                    {"option_id": f"opt_{i}_a", "option_text": "Option A", "is_correct": False},
                    {"option_id": f"opt_{i}_b", "option_text": "Option B", "is_correct": True},
                    {"option_id": f"opt_{i}_c", "option_text": "Option C", "is_correct": False},
                    {"option_id": f"opt_{i}_d", "option_text": "Option D", "is_correct": False}
                ],
                "explanation": f"Option B is correct because it best represents the key concept in {assessment_spec.subject_area}."
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_true_false_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate true/false questions"""
        questions = []
        
        for i in range(count):
            is_true = i % 2 == 0  # Alternate between true and false
            question_data = {
                "question_id": f"tf_{uuid.uuid4().hex[:8]}",
                "question_text": f"True or False: {assessment_spec.subject_area} concepts are fundamental to the field.",
                "question_type": QuestionType.TRUE_FALSE,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 3.0,
                "correct_answer": is_true,
                "explanation": f"This statement is {'true' if is_true else 'false'} because {assessment_spec.subject_area} plays a crucial role in understanding the field."
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_short_answer_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate short answer questions"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question_id": f"sa_{uuid.uuid4().hex[:8]}",
                "question_text": f"Briefly explain the importance of {assessment_spec.subject_area} in modern applications.",
                "question_type": QuestionType.SHORT_ANSWER,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 8.0,
                "sample_answer": f"Key points about {assessment_spec.subject_area} importance include applications, benefits, and relevance to current practices.",
                "key_points": [
                    "Practical applications",
                    "Industry relevance",
                    "Future implications",
                    "Problem-solving capabilities"
                ]
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_essay_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate essay questions"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question_id": f"essay_{uuid.uuid4().hex[:8]}",
                "question_text": f"Write a comprehensive essay analyzing the role of {assessment_spec.subject_area} in contemporary society. Address key themes, challenges, and future directions.",
                "question_type": QuestionType.ESSAY,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 25.0,
                "word_limit": "500-750 words",
                "evaluation_criteria": [
                    "Content accuracy and depth",
                    "Organization and structure",
                    "Analysis and critical thinking",
                    "Writing quality and clarity"
                ],
                "sample_answer": "A sample essay would address multiple aspects of the topic with clear structure and insightful analysis."
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_calculation_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate calculation questions"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question_id": f"calc_{uuid.uuid4().hex[:8]}",
                "question_text": f"Calculate the impact factor for {assessment_spec.subject_area} given the following parameters: citations = {100 + i * 20}, publications = {10 + i * 2}.",
                "question_type": QuestionType.CALCULATION,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 15.0,
                "formula": "Impact Factor = Total Citations / Total Publications",
                "sample_calculation": f"Impact Factor = {100 + i * 20} / {10 + i * 2} = {(100 + i * 20) / (10 + i * 2):.2f}",
                "correct_answer": (100 + i * 20) / (10 + i * 2)
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_case_study_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate case study questions"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question_id": f"case_{uuid.uuid4().hex[:8]}",
                "question_text": f"Read the following case study about {assessment_spec.subject_area} implementation and provide your analysis and recommendations.",
                "question_type": QuestionType.CASE_STUDY,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 20.0,
                "case_study": {
                    "scenario": f"A company is implementing {assessment_spec.subject_area} solutions and faces several challenges...",
                    "challenges": [
                        "Budget constraints",
                        "Technical limitations",
                        "Stakeholder resistance",
                        "Timeline pressure"
                    ],
                    "questions": [
                        "What are the main challenges identified?",
                        "How would you prioritize these challenges?",
                        "What solutions would you recommend?"
                    ]
                },
                "evaluation_rubric": {
                    "analysis_quality": 5,
                    "solution_feasibility": 5,
                    "implementation_plan": 5,
                    "critical_thinking": 5
                }
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_research_questions(self, assessment_spec: AssessmentSpec, count: int) -> List[Dict[str, Any]]:
        """Generate research questions"""
        questions = []
        
        for i in range(count):
            question_data = {
                "question_id": f"research_{uuid.uuid4().hex[:8]}",
                "question_text": f"Conduct research on current trends in {assessment_spec.subject_area} and present your findings.",
                "question_type": QuestionType.ESSAY,
                "difficulty_level": assessment_spec.difficulty_level,
                "points": 30.0,
                "research_requirements": [
                    "Minimum 5 credible sources",
                    "Recent publications (last 5 years)",
                    "Multiple perspectives included",
                    "Original analysis presented"
                ],
                "deliverables": [
                    "Research paper (1000-1500 words)",
                    "Bibliography with proper citations",
                    "Summary of key findings",
                    "Implications and recommendations"
                ]
            }
            questions.append(question_data)
        
        return questions
    
    async def _generate_quick_questions(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate quick assessment questions"""
        questions = []
        
        for i in range(count):
            if i % 3 == 0:
                # Multiple choice
                question = await self._create_quick_multiple_choice(topic)
            elif i % 3 == 1:
                # True/False
                question = await self._create_quick_true_false(topic)
            else:
                # Short answer
                question = await self._create_quick_short_answer(topic)
            
            questions.append(question)
        
        return questions
    
    async def _create_quick_multiple_choice(self, topic: str) -> Dict[str, Any]:
        """Create quick multiple choice question"""
        return {
            "question_id": f"quick_mc_{uuid.uuid4().hex[:8]}",
            "question_text": f"What is the most important aspect of {topic}?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "difficulty_level": DifficultyLevel.INTERMEDIATE,
            "points": 5.0,
            "options": [
                {"option_id": "mc_a", "option_text": "Understanding fundamentals", "is_correct": True},
                {"option_id": "mc_b", "option_text": "Memorizing facts", "is_correct": False},
                {"option_id": "mc_c", "option_text": "Speed of completion", "is_correct": False},
                {"option_id": "mc_d", "option_text": "Getting good grades", "is_correct": False}
            ]
        }
    
    async def _create_quick_true_false(self, topic: str) -> Dict[str, Any]:
        """Create quick true/false question"""
        return {
            "question_id": f"quick_tf_{uuid.uuid4().hex[:8]}",
            "question_text": f"True or False: {topic} requires continuous learning and adaptation.",
            "question_type": QuestionType.TRUE_FALSE,
            "difficulty_level": DifficultyLevel.BASIC,
            "points": 3.0,
            "correct_answer": True,
            "explanation": f"{topic} is an evolving field that requires continuous learning to stay current."
        }
    
    async def _create_quick_short_answer(self, topic: str) -> Dict[str, Any]:
        """Create quick short answer question"""
        return {
            "question_id": f"quick_sa_{uuid.uuid4().hex[:8]}",
            "question_text": f"In one sentence, explain why {topic} is relevant today.",
            "question_type": QuestionType.SHORT_ANSWER,
            "difficulty_level": DifficultyLevel.BASIC,
            "points": 4.0,
            "key_points": [
                "Current relevance",
                "Practical applications",
                "Future importance"
            ]
        }
    
    async def _create_assessment_structure(self, assessment_spec: AssessmentSpec) -> Dict[str, Any]:
        """Create assessment structure"""
        return {
            "assessment_id": assessment_spec.spec_id,
            "title": assessment_spec.title,
            "description": assessment_spec.description,
            "instructions": await self._generate_assessment_instructions(assessment_spec),
            "sections": await self._create_assessment_sections(assessment_spec),
            "technical_requirements": {
                "time_limit_minutes": assessment_spec.time_limit_minutes,
                "max_attempts": assessment_spec.max_attempts,
                "browser_requirements": "Modern web browser",
                "internet_connection": "Required for submission"
            }
        }
    
    async def _generate_assessment_instructions(self, assessment_spec: AssessmentSpec) -> List[str]:
        """Generate assessment instructions"""
        instructions = [
            f"Welcome to the {assessment_spec.title} assessment.",
            f"This {assessment_spec.assessment_type.value} covers {assessment_spec.subject_area}.",
            f"You have {assessment_spec.time_limit_minutes} minutes to complete this assessment.",
            f"You have {assessment_spec.max_attempts} attempt(s) available.",
            f"Passing score: {assessment_spec.passing_score}%"
        ]
        
        if assessment_spec.randomize_questions:
            instructions.append("Questions will be presented in random order.")
        
        if assessment_spec.immediate_feedback:
            instructions.append("You will receive immediate feedback after each question.")
        
        return instructions
    
    async def _create_assessment_sections(self, assessment_spec: AssessmentSpec) -> List[Dict[str, Any]]:
        """Create assessment sections"""
        sections = []
        
        # Group questions by type
        questions_by_type = defaultdict(list)
        for question in assessment_spec.questions:
            questions_by_type[question["question_type"]].append(question)
        
        for question_type, questions in questions_by_type.items():
            section = {
                "section_name": question_type.value.replace("_", " ").title(),
                "question_count": len(questions),
                "total_points": sum(q.get("points", 0) for q in questions),
                "instructions": f"Complete all {question_type.value.replace('_', ' ')} questions in this section.",
                "questions": questions
            }
            sections.append(section)
        
        return sections
    
    async def _validate_assessment(self, assessment_spec: AssessmentSpec) -> Dict[str, Any]:
        """Validate assessment specification"""
        validation_results = {
            "is_valid": True,
            "validation_errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Validate required fields
        if not assessment_spec.title:
            validation_results["validation_errors"].append("Assessment title is required")
            validation_results["is_valid"] = False
        
        if not assessment_spec.questions:
            validation_results["validation_errors"].append("At least one question is required")
            validation_results["is_valid"] = False
        
        # Validate time limits
        if assessment_spec.time_limit_minutes < 10:
            validation_results["warnings"].append("Time limit seems very short (< 10 minutes)")
        
        if assessment_spec.time_limit_minutes > 300:
            validation_results["warnings"].append("Time limit seems very long (> 5 hours)")
        
        # Validate question count
        if len(assessment_spec.questions) < 5:
            validation_results["recommendations"].append("Consider adding more questions for better coverage")
        
        # Validate difficulty distribution
        difficulty_counts = defaultdict(int)
        for question in assessment_spec.questions:
            difficulty_counts[question.get("difficulty_level", DifficultyLevel.INTERMEDIATE)] += 1
        
        if difficulty_counts[DifficultyLevel.BASIC] / len(assessment_spec.questions) > 0.8:
            validation_results["recommendations"].append("Assessment may be too easy - consider adding harder questions")
        
        return validation_results
    
    async def _generate_question_set(self, topic: str, question_type: QuestionType, difficulty: DifficultyLevel) -> List[Question]:
        """Generate a set of questions for specific criteria"""
        questions = []
        
        # Generate 2-3 questions per combination
        for i in range(2):
            question = Question(
                question_text=f"Question about {topic} - {question_type.value} - {difficulty.value}",
                question_type=question_type,
                difficulty_level=difficulty,
                points=5.0 if difficulty == DifficultyLevel.BASIC else 10.0 if difficulty == DifficultyLevel.INTERMEDIATE else 15.0,
                tags=[topic, question_type.value, difficulty.value]
            )
            questions.append(question)
        
        return questions
    
    async def _analyze_question_complexity(self, question: Question) -> Dict[str, Any]:
        """Analyze complexity of a question"""
        # Simple complexity analysis based on text length and structure
        text_length = len(question.question_text.split())
        has_multiple_parts = ";" in question.question_text or "and" in question.question_text
        
        complexity_score = min(1.0, (text_length / 50) + (0.3 if has_multiple_parts else 0))
        
        return {
            "complexity_score": complexity_score,
            "text_length": text_length,
            "has_multiple_parts": has_multiple_parts,
            "complexity_level": "high" if complexity_score > 0.7 else "medium" if complexity_score > 0.4 else "low"
        }
    
    async def _assess_learning_objective_alignment(self, question: Question, learning_objectives: List[str]) -> float:
        """Assess alignment with learning objectives"""
        if not learning_objectives:
            return 0.5  # Neutral score if no objectives provided
        
        # Simple alignment check based on keyword matching
        question_words = set(question.question_text.lower().split())
        alignment_score = 0.0
        
        for objective in learning_objectives:
            objective_words = set(objective.lower().split())
            overlap = len(question_words.intersection(objective_words))
            if overlap > 0:
                alignment_score = max(alignment_score, overlap / len(objective_words))
        
        return min(1.0, alignment_score)
    
    async def _assess_question_clarity(self, question: Question) -> float:
        """Assess clarity of question"""
        # Simple clarity metrics
        text = question.question_text
        
        # Check for clarity indicators
        clarity_indicators = {
            "has_question_mark": "?" in text,
            "reasonable_length": 10 <= len(text.split()) <= 100,
            "no_redundancy": text.count("?") <= 1,
            "clear_language": not any(word in text.lower() for word in ["um", "uh", "like", "you know"])
        }
        
        clarity_score = sum(clarity_indicators.values()) / len(clarity_indicators)
        return clarity_score
    
    async def _generate_question_improvement_suggestions(self, question: Question, complexity_analysis: Dict[str, Any], alignment_score: float, clarity_score: float) -> List[str]:
        """Generate suggestions for improving questions"""
        suggestions = []
        
        if complexity_analysis["complexity_score"] < 0.3:
            suggestions.append("Consider adding more depth to the question")
        elif complexity_analysis["complexity_score"] > 0.8:
            suggestions.append("Question may be too complex - consider breaking it down")
        
        if alignment_score < 0.5:
            suggestions.append("Ensure question aligns with stated learning objectives")
        
        if clarity_score < 0.7:
            suggestions.append("Improve clarity by simplifying language and structure")
        
        if not suggestions:
            suggestions.append("Question quality is good - no immediate improvements needed")
        
        return suggestions


class EvaluationEngine:
    """Engine for evaluating assessments and providing feedback"""
    
    def __init__(self):
        self.grading_cache: Dict[str, Dict[str, Any]] = {}
    
    async def evaluate_assessment_submission(
        self, 
        assessment_id: str, 
        answers: List[Dict[str, Any]], 
        time_spent_minutes: int
    ) -> AssessmentResult:
        """Evaluate a complete assessment submission"""
        try:
            logger.info(f"Evaluating assessment submission: {assessment_id}")
            
            start_time = datetime.utcnow()
            
            # Calculate scores for each answer
            individual_scores = []
            total_score = 0.0
            max_score = 0.0
            
            for answer in answers:
                question_id = answer.get("question_id")
                response = answer.get("response")
                
                question_score = await self._evaluate_individual_answer(question_id, response)
                individual_scores.append(question_score)
                total_score += question_score["points_earned"]
                max_score += question_score["max_points"]
            
            # Calculate percentage and grade
            percentage_score = (total_score / max_score * 100) if max_score > 0 else 0
            grade = self._calculate_grade(percentage_score)
            
            # Generate comprehensive feedback
            feedback = await self._generate_comprehensive_feedback(answers, individual_scores)
            
            # Create assessment result
            result = AssessmentResult(
                result_id=f"result_{uuid.uuid4().hex[:8]}",
                assessment_id=assessment_id,
                student_id="anonymous",  # Would be provided in real implementation
                total_score=total_score,
                max_score=max_score,
                percentage_score=percentage_score,
                grade=grade,
                time_spent_minutes=time_spent_minutes,
                answers=answers,
                feedback=feedback
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Assessment evaluation failed: {e}")
            # Return error result
            return AssessmentResult(
                result_id=f"error_result_{uuid.uuid4().hex[:8]}",
                assessment_id=assessment_id,
                student_id="anonymous",
                total_score=0.0,
                max_score=100.0,
                percentage_score=0.0,
                grade="F",
                time_spent_minutes=time_spent_minutes,
                answers=answers,
                feedback={"error": str(e)}
            )
    
    async def evaluate_individual_question(self, question: Dict[str, Any], response: Any) -> Dict[str, Any]:
        """Evaluate response to individual question"""
        try:
            question_type = question.get("question_type")
            
            if question_type == QuestionType.MULTIPLE_CHOICE.value:
                return await self._evaluate_multiple_choice(question, response)
            elif question_type == QuestionType.TRUE_FALSE.value:
                return await self._evaluate_true_false(question, response)
            elif question_type == QuestionType.SHORT_ANSWER.value:
                return await self._evaluate_short_answer(question, response)
            elif question_type == QuestionType.ESSAY.value:
                return await self._evaluate_essay(question, response)
            elif question_type == QuestionType.CALCULATION.value:
                return await self._evaluate_calculation(question, response)
            else:
                return await self._evaluate_generic_question(question, response)
                
        except Exception as e:
            logger.error(f"Question evaluation failed: {e}")
            return {
                "points_earned": 0.0,
                "max_points": question.get("points", 1.0),
                "is_correct": False,
                "feedback": f"Error evaluating question: {str(e)}"
            }
    
    async def _evaluate_individual_answer(self, question_id: str, response: Any) -> Dict[str, Any]:
        """Evaluate individual answer (placeholder implementation)"""
        # In a real implementation, this would fetch the question from database
        # and call the appropriate evaluation method
        
        return {
            "question_id": question_id,
            "points_earned": 5.0,  # Placeholder
            "max_points": 10.0,    # Placeholder
            "is_correct": True,    # Placeholder
            "feedback": "Well done!"  # Placeholder
        }
    
    async def _evaluate_multiple_choice(self, question: Dict[str, Any], response: Any) -> Dict[str, Any]:
        """Evaluate multiple choice response"""
        selected_option = response.get("selected_option_id") if isinstance(response, dict) else response
        
        # Find correct option
        correct_option = None
        for option in question.get("options", []):
            if option.get("is_correct", False):
                correct_option = option.get("option_id")
                break
        
        is_correct = selected_option == correct_option
        points_earned = question.get("points", 1.0) if is_correct else 0.0
        
        # Get feedback
        feedback = "Correct answer!" if is_correct else f"Incorrect. The correct answer is: {correct_option}"
        
        return {
            "points_earned": points_earned,
            "max_points": question.get("points", 1.0),
            "is_correct": is_correct,
            "feedback": feedback,
            "correct_answer": correct_option
        }
    
    async def _evaluate_true_false(self, question: Dict[str, Any], response: Any) -> Dict[str, Any]:
        """Evaluate true/false response"""
        response_value = response if isinstance(response, bool) else bool(response)
        correct_answer = question.get("correct_answer", False)
        
        is_correct = response_value == correct_answer
        points_earned = question.get("points", 1.0) if is_correct else 0.0
        
        return {
            "points_earned": points_earned,
            "max_points": question.get("points", 1.0),
            "is_correct": is_correct,
            "feedback": f"Correct! The answer is {correct_answer}." if is_correct else f"Incorrect. The correct answer is {correct_answer}.",
            "correct_answer": correct_answer
        }
    
    async def _evaluate_short_answer(self, question: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Evaluate short answer response"""
        response_text = str(response).lower().strip()
        key_points = question.get("key_points", [])
        
        # Simple keyword matching for scoring
        points_earned = 0.0
        max_points = question.get("points", 1.0)
        
        if key_points:
            for point in key_points:
                if point.lower() in response_text:
                    points_earned += max_points / len(key_points)
        else:
            # If no key points defined, give partial credit for reasonable length
            if len(response_text.split()) > 5:
                points_earned = max_points * 0.7
            elif len(response_text.split()) > 2:
                points_earned = max_points * 0.4
        
        is_correct = points_earned >= max_points * 0.6
        
        return {
            "points_earned": min(points_earned, max_points),
            "max_points": max_points,
            "is_correct": is_correct,
            "feedback": await self._generate_short_answer_feedback(question, response_text, points_earned, max_points)
        }
    
    async def _evaluate_essay(self, question: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Evaluate essay response"""
        response_text = str(response)
        word_count = len(response_text.split())
        max_points = question.get("points", 1.0)
        
        # Basic scoring based on length and structure
        if word_count < 50:
            points_earned = max_points * 0.2
        elif word_count < 200:
            points_earned = max_points * 0.6
        elif word_count < 500:
            points_earned = max_points * 0.8
        else:
            points_earned = max_points * 0.9
        
        # Check for structure indicators
        structure_score = 0.0
        if any(indicator in response_text.lower() for indicator in ["introduction", "conclusion", "however", "therefore"]):
            structure_score = 0.2
        points_earned += structure_score
        
        is_correct = points_earned >= max_points * 0.5
        
        return {
            "points_earned": min(points_earned, max_points),
            "max_points": max_points,
            "is_correct": is_correct,
            "feedback": await self._generate_essay_feedback(question, response_text, word_count, points_earned, max_points),
            "word_count": word_count,
            "structure_score": structure_score
        }
    
    async def _evaluate_calculation(self, question: Dict[str, Any], response: Any) -> Dict[str, Any]:
        """Evaluate calculation response"""
        try:
            response_value = float(response) if isinstance(response, (int, float)) else float(str(response))
            correct_answer = question.get("correct_answer")
            
            # Allow for small numerical differences
            tolerance = 0.01
            is_correct = abs(response_value - correct_answer) <= tolerance
            points_earned = question.get("points", 1.0) if is_correct else 0.0
            
            return {
                "points_earned": points_earned,
                "max_points": question.get("points", 1.0),
                "is_correct": is_correct,
                "feedback": f"Calculation correct! Answer: {correct_answer}" if is_correct else f"Incorrect. Correct answer: {correct_answer}",
                "correct_answer": correct_answer,
                "student_answer": response_value
            }
        except (ValueError, TypeError):
            return {
                "points_earned": 0.0,
                "max_points": question.get("points", 1.0),
                "is_correct": False,
                "feedback": "Invalid numerical input. Please provide a number.",
                "student_answer": response
            }
    
    async def _evaluate_generic_question(self, question: Dict[str, Any], response: Any) -> Dict[str, Any]:
        """Evaluate generic question response"""
        # Default evaluation for unknown question types
        max_points = question.get("points", 1.0)
        
        # Give partial credit for any response
        points_earned = max_points * 0.5 if response else 0.0
        is_correct = points_earned > 0
        
        return {
            "points_earned": points_earned,
            "max_points": max_points,
            "is_correct": is_correct,
            "feedback": "Response received and evaluated.",
            "question_type": question.get("question_type", "unknown")
        }
    
    async def _generate_comprehensive_feedback(self, answers: List[Dict[str, Any]], individual_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive feedback"""
        total_questions = len(answers)
        correct_answers = sum(1 for score in individual_scores if score.get("is_correct", False))
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0
        
        # Identify areas for improvement
        weak_areas = []
        strong_areas = []
        
        for i, score in enumerate(individual_scores):
            if i < len(answers):
                question_type = answers[i].get("question_type", "unknown")
                if score.get("is_correct", False):
                    if question_type not in strong_areas:
                        strong_areas.append(question_type)
                else:
                    if question_type not in weak_areas:
                        weak_areas.append(question_type)
        
        return {
            "accuracy_rate": accuracy_rate,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "strong_areas": strong_areas,
            "weak_areas": weak_areas,
            "performance_level": self._determine_performance_level(accuracy_rate),
            "study_recommendations": self._generate_study_recommendations(weak_areas),
            "next_steps": self._generate_next_steps(accuracy_rate)
        }
    
    async def _generate_short_answer_feedback(self, question: Dict[str, Any], response: str, points_earned: float, max_points: float) -> str:
        """Generate feedback for short answer questions"""
        if points_earned >= max_points * 0.8:
            return "Excellent response! You covered the key points comprehensively."
        elif points_earned >= max_points * 0.6:
            return "Good response. Consider expanding on some key points for a more complete answer."
        elif points_earned >= max_points * 0.3:
            return "Partial credit awarded. Review the key concepts and try to include more relevant details."
        else:
            return "Response needs improvement. Make sure to address the main points of the question."
    
    async def _generate_essay_feedback(self, question: Dict[str, Any], response: str, word_count: int, points_earned: float, max_points: float) -> str:
        """Generate feedback for essay questions"""
        feedback_parts = []
        
        if word_count < 100:
            feedback_parts.append("Essay is too short. Aim for more comprehensive coverage of the topic.")
        elif word_count > 800:
            feedback_parts.append("Essay is quite long. Focus on conciseness while maintaining depth.")
        else:
            feedback_parts.append("Essay length is appropriate.")
        
        if points_earned >= max_points * 0.8:
            feedback_parts.append("Excellent analysis and writing quality.")
        elif points_earned >= max_points * 0.6:
            feedback_parts.append("Good effort with room for improvement in analysis depth.")
        else:
            feedback_parts.append("Consider improving organization and analytical depth.")
        
        return " ".join(feedback_parts)
    
    def _calculate_grade(self, percentage_score: float) -> str:
        """Calculate letter grade from percentage"""
        if percentage_score >= 90:
            return "A"
        elif percentage_score >= 80:
            return "B"
        elif percentage_score >= 70:
            return "C"
        elif percentage_score >= 60:
            return "D"
        else:
            return "F"
    
    def _determine_performance_level(self, accuracy_rate: float) -> str:
        """Determine performance level from accuracy rate"""
        if accuracy_rate >= 0.9:
            return "Excellent"
        elif accuracy_rate >= 0.8:
            return "Good"
        elif accuracy_rate >= 0.7:
            return "Satisfactory"
        elif accuracy_rate >= 0.6:
            return "Needs Improvement"
        else:
            return "Unsatisfactory"
    
    def _generate_study_recommendations(self, weak_areas: List[str]) -> List[str]:
        """Generate study recommendations based on weak areas"""
        recommendations = []
        
        for area in weak_areas:
            if area == "multiple_choice":
                recommendations.append("Practice identifying key concepts and distinctions")
            elif area == "short_answer":
                recommendations.append("Review key terms and practice concise explanations")
            elif area == "essay":
                recommendations.append("Work on analytical writing and essay structure")
            elif area == "calculation":
                recommendations.append("Practice problem-solving and computational skills")
            else:
                recommendations.append(f"Focus additional study on {area.replace('_', ' ')}")
        
        if not recommendations:
            recommendations.append("Continue current study practices")
        
        return recommendations
    
    def _generate_next_steps(self, accuracy_rate: float) -> List[str]:
        """Generate next steps based on performance"""
        if accuracy_rate >= 0.9:
            return [
                "Consider advanced topics in this subject area",
                "Explore real-world applications",
                "Help peers with challenging concepts"
            ]
        elif accuracy_rate >= 0.7:
            return [
                "Review areas where answers were incorrect",
                "Practice with additional sample questions",
                "Seek clarification on misunderstood concepts"
            ]
        else:
            return [
                "Review fundamental concepts thoroughly",
                "Consider seeking additional help or tutoring",
                "Practice regularly with easier questions first",
                "Schedule follow-up assessment after study period"
            ]


class RubricGenerator:
    """Generator for assessment rubrics"""
    
    def __init__(self):
        self.rubric_templates = self._load_rubric_templates()
    
    def _load_rubric_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load rubric templates for different assessment types"""
        return {
            AssessmentType.ASSIGNMENT.value: {
                "criteria": [
                    {"name": "Content Quality", "description": "Accuracy and depth of content", "weight": 0.4},
                    {"name": "Organization", "description": "Structure and logical flow", "weight": 0.2},
                    {"name": "Writing Quality", "description": "Clarity and grammar", "weight": 0.2},
                    {"name": "Creativity", "description": "Original thinking and innovation", "weight": 0.2}
                ],
                "performance_levels": [
                    {"level": "Excellent", "score": 4, "description": "Exceeds expectations"},
                    {"level": "Good", "score": 3, "description": "Meets expectations"},
                    {"level": "Satisfactory", "score": 2, "description": "Partially meets expectations"},
                    {"level": "Needs Improvement", "score": 1, "description": "Does not meet expectations"}
                ]
            },
            AssessmentType.PROJECT.value: {
                "criteria": [
                    {"name": "Research Quality", "description": "Depth and breadth of research", "weight": 0.3},
                    {"name": "Implementation", "description": "Quality of execution", "weight": 0.3},
                    {"name": "Presentation", "description": "Clarity of communication", "weight": 0.2},
                    {"name": "Innovation", "description": "Creative problem-solving", "weight": 0.2}
                ],
                "performance_levels": [
                    {"level": "Outstanding", "score": 5, "description": "Exceptional quality"},
                    {"level": "Proficient", "score": 4, "description": "High quality"},
                    {"level": "Competent", "score": 3, "description": "Satisfactory quality"},
                    {"level": "Developing", "score": 2, "description": "Basic quality"},
                    {"level": "Beginning", "score": 1, "description": "Minimal quality"}
                ]
            }
        }
    
    async def create_rubric(self, assessment_spec: AssessmentSpec) -> Dict[str, Any]:
        """Create rubric for assessment"""
        try:
            logger.info(f"Creating rubric for: {assessment_spec.title}")
            
            # Get template for assessment type
            template = self.rubric_templates.get(assessment_spec.assessment_type.value, self._get_default_template())
            
            # Create rubric criteria
            criteria = []
            for criterion_data in template["criteria"]:
                criterion = RubricCriterion(
                    name=criterion_data["name"],
                    description=criterion_data["description"],
                    max_points=criterion_data["weight"] * 100,  # Scale to 100 points
                    performance_levels=template["performance_levels"],
                    weight=criterion_data["weight"]
                )
                criteria.append(criterion)
            
            # Create rubric structure
            rubric = {
                "rubric_id": f"rubric_{uuid.uuid4().hex[:8]}",
                "assessment_id": assessment_spec.spec_id,
                "title": f"Rubric for {assessment_spec.title}",
                "description": f"Evaluation criteria for {assessment_spec.assessment_type.value} in {assessment_spec.subject_area}",
                "criteria": [criterion.__dict__ for criterion in criteria],
                "total_points": sum(criterion.max_points for criterion in criteria),
                "grading_scale": assessment_spec.grading_scale.value,
                "instructions": await self._generate_rubric_instructions(assessment_spec),
                "created_at": datetime.utcnow().isoformat()
            }
            
            return rubric
            
        except Exception as e:
            logger.error(f"Rubric creation failed: {e}")
            return {
                "error": str(e),
                "assessment_spec": assessment_spec.__dict__ if hasattr(assessment_spec, '__dict__') else {}
            }
    
    def _get_default_template(self) -> Dict[str, Any]:
        """Get default rubric template"""
        return {
            "criteria": [
                {"name": "Content Accuracy", "description": "Correctness of information", "weight": 0.4},
                {"name": "Completeness", "description": "Coverage of required elements", "weight": 0.3},
                {"name": "Quality", "description": "Overall quality of work", "weight": 0.3}
            ],
            "performance_levels": [
                {"level": "Excellent", "score": 4, "description": "Exceeds expectations"},
                {"level": "Good", "score": 3, "description": "Meets expectations"},
                {"level": "Satisfactory", "score": 2, "description": "Partially meets expectations"},
                {"level": "Needs Improvement", "score": 1, "description": "Does not meet expectations"}
            ]
        }
    
    async def _generate_rubric_instructions(self, assessment_spec: AssessmentSpec) -> List[str]:
        """Generate instructions for rubric usage"""
        return [
            f"Evaluate this {assessment_spec.assessment_type.value} using the criteria below.",
            f"Each criterion should be assessed independently.",
            f"Scores reflect the student's performance on each criterion.",
            f"Total score determines the final grade.",
            f"Use the performance level descriptions to guide your evaluation."
        ]


class AssessmentAnalyticsEngine:
    """Engine for comprehensive assessment analytics"""
    
    def __init__(self):
        self.analytics_cache: Dict[str, AssessmentAnalytics] = {}
    
    async def generate_assessment_analytics(self, assessment_id: str, results: List[AssessmentResult]) -> AssessmentAnalytics:
        """Generate comprehensive analytics for assessment"""
        try:
            logger.info(f"Generating analytics for assessment: {assessment_id}")
            
            if not results:
                return self._create_empty_analytics(assessment_id)
            
            # Calculate basic statistics
            scores = [result.percentage_score for result in results]
            total_participants = len(results)
            average_score = statistics.mean(scores)
            
            # Calculate completion rate
            completion_rate = 1.0  # Assuming all submitted results are complete
            
            # Generate score distribution
            score_distribution = self._generate_score_distribution(scores)
            
            # Analyze difficulty
            difficulty_analysis = await self._analyze_assessment_difficulty(results)
            
            # Perform item analysis
            item_analysis = await self._perform_item_analysis(results)
            
            # Generate recommendations
            recommendations = await self._generate_analytics_recommendations(
                average_score, score_distribution, difficulty_analysis, item_analysis
            )
            
            analytics = AssessmentAnalytics(
                assessment_id=assessment_id,
                total_participants=total_participants,
                completion_rate=completion_rate,
                average_score=average_score,
                score_distribution=score_distribution,
                difficulty_analysis=difficulty_analysis,
                item_analysis=item_analysis,
                recommendations=recommendations
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return self._create_empty_analytics(assessment_id)
    
    async def analyze_student_performance(self, student_id: str, assessment_results: List[AssessmentResult]) -> StudentPerformance:
        """Analyze individual student performance"""
        try:
            logger.info(f"Analyzing performance for student: {student_id}")
            
            if not assessment_results:
                return StudentPerformance(student_id=student_id)
            
            # Calculate overall performance score
            scores = [result.percentage_score for result in assessment_results]
            overall_performance_score = statistics.mean(scores)
            
            # Identify skill progression over time
            skill_progression = await self._calculate_skill_progression(assessment_results)
            
            # Identify strengths and weaknesses
            performance_by_type = defaultdict(list)
            for result in assessment_results:
                # Group by assessment type (would need to be stored in results)
                assessment_type = getattr(result, 'assessment_type', 'unknown')
                performance_by_type[assessment_type].append(result.percentage_score)
            
            areas_of_strength = []
            areas_for_improvement = []
            
            for assessment_type, type_scores in performance_by_type.items():
                avg_score = statistics.mean(type_scores)
                if avg_score >= 80:
                    areas_of_strength.append(assessment_type)
                elif avg_score < 70:
                    areas_for_improvement.append(assessment_type)
            
            performance = StudentPerformance(
                student_id=student_id,
                assessment_results=assessment_results,
                skill_progression=skill_progression,
                areas_of_strength=areas_of_strength,
                areas_for_improvement=areas_for_improvement,
                overall_performance_score=overall_performance_score
            )
            
            return performance
            
        except Exception as e:
            logger.error(f"Student performance analysis failed: {e}")
            return StudentPerformance(student_id=student_id)
    
    async def compare_cohort_performance(self, cohort_results: Dict[str, List[AssessmentResult]]) -> Dict[str, Any]:
        """Compare performance across different cohorts"""
        try:
            logger.info("Comparing cohort performance")
            
            cohort_comparisons = {}
            
            for cohort_name, results in cohort_results.items():
                if results:
                    scores = [result.percentage_score for result in results]
                    cohort_comparisons[cohort_name] = {
                        "average_score": statistics.mean(scores),
                        "median_score": statistics.median(scores),
                        "score_range": [min(scores), max(scores)],
                        "standard_deviation": statistics.stdev(scores) if len(scores) > 1 else 0,
                        "participant_count": len(results)
                    }
            
            # Identify top and bottom performing cohorts
            avg_scores = {name: data["average_score"] for name, data in cohort_comparisons.items()}
            top_cohort = max(avg_scores, key=avg_scores.get) if avg_scores else None
            bottom_cohort = min(avg_scores, key=avg_scores.get) if avg_scores else None
            
            return {
                "cohort_comparisons": cohort_comparisons,
                "top_performing_cohort": top_cohort,
                "bottom_performing_cohort": bottom_cohort,
                "performance_gap": avg_scores.get(top_cohort, 0) - avg_scores.get(bottom_cohort, 0) if top_cohort and bottom_cohort else 0,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cohort comparison failed: {e}")
            return {
                "error": str(e),
                "cohort_comparisons": {}
            }
    
    def _create_empty_analytics(self, assessment_id: str) -> AssessmentAnalytics:
        """Create empty analytics object"""
        return AssessmentAnalytics(
            assessment_id=assessment_id,
            total_participants=0,
            completion_rate=0.0,
            average_score=0.0,
            score_distribution={"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            difficulty_analysis={"too_easy": 0.0, "appropriate": 0.0, "too_hard": 0.0},
            item_analysis=[],
            recommendations=["No data available for analysis"]
        )
    
    def _generate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Generate score distribution by letter grade"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        for score in scores:
            if score >= 90:
                distribution["A"] += 1
            elif score >= 80:
                distribution["B"] += 1
            elif score >= 70:
                distribution["C"] += 1
            elif score >= 60:
                distribution["D"] += 1
            else:
                distribution["F"] += 1
        
        return distribution
    
    async def _analyze_assessment_difficulty(self, results: List[AssessmentResult]) -> Dict[str, float]:
        """Analyze assessment difficulty based on results"""
        if not results:
            return {"too_easy": 0.0, "appropriate": 0.0, "too_hard": 0.0}
        
        scores = [result.percentage_score for result in results]
        average_score = statistics.mean(scores)
        
        # Classify difficulty based on average score
        if average_score >= 85:
            return {"too_easy": 1.0, "appropriate": 0.0, "too_hard": 0.0}
        elif average_score >= 70:
            return {"too_easy": 0.2, "appropriate": 0.8, "too_hard": 0.0}
        elif average_score >= 55:
            return {"too_easy": 0.0, "appropriate": 0.7, "too_hard": 0.3}
        else:
            return {"too_easy": 0.0, "appropriate": 0.3, "too_hard": 0.7}
    
    async def _perform_item_analysis(self, results: List[AssessmentResult]) -> List[Dict[str, Any]]:
        """Perform statistical analysis of individual questions"""
        # Placeholder implementation
        # In a real implementation, this would analyze each question
        item_analysis = []
        
        # Mock analysis for demonstration
        for i in range(5):  # Assume 5 questions
            item_data = {
                "question_id": f"q_{i+1}",
                "difficulty_index": 0.5 + (i * 0.1),  # Mock difficulty
                "discrimination_index": 0.3 + (i * 0.05),  # Mock discrimination
                "point_biserial": 0.4 + (i * 0.03),  # Mock correlation
                "performance_rate": 0.7 - (i * 0.05)  # Mock success rate
            }
            item_analysis.append(item_data)
        
        return item_analysis
    
    async def _generate_analytics_recommendations(
        self, 
        average_score: float, 
        score_distribution: Dict[str, int], 
        difficulty_analysis: Dict[str, float], 
        item_analysis: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        # Difficulty recommendations
        if difficulty_analysis["too_easy"] > 0.5:
            recommendations.append("Consider making the assessment more challenging")
        elif difficulty_analysis["too_hard"] > 0.5:
            recommendations.append("Consider reducing difficulty or providing more preparation materials")
        
        # Score distribution recommendations
        if score_distribution["F"] > score_distribution["A"]:
            recommendations.append("High failure rate detected - review content coverage and student preparation")
        
        if score_distribution["A"] > 0.6:
            recommendations.append("High success rate - consider adding more challenging questions")
        
        # Item analysis recommendations
        for item in item_analysis:
            if item["performance_rate"] > 0.9:
                recommendations.append(f"Question {item['question_id']} may be too easy - consider revision")
            elif item["performance_rate"] < 0.3:
                recommendations.append(f"Question {item['question_id']} may be too difficult - review content coverage")
        
        if not recommendations:
            recommendations.append("Assessment performance is within acceptable ranges")
        
        return recommendations
    
    async def _calculate_skill_progression(self, assessment_results: List[AssessmentResult]) -> Dict[str, float]:
        """Calculate skill progression over time"""
        # Placeholder implementation
        # In a real implementation, this would track specific skills
        skill_progression = {
            "overall_performance": 0.0,
            "content_mastery": 0.0,
            "application_skills": 0.0,
            "critical_thinking": 0.0
        }
        
        if assessment_results:
            scores = [result.percentage_score for result in assessment_results]
            overall_trend = (scores[-1] - scores[0]) / len(scores) if len(scores) > 1 else 0
            
            skill_progression["overall_performance"] = statistics.mean(scores)
            skill_progression["content_mastery"] = min(100, skill_progression["overall_performance"] + overall_trend * 2)
            skill_progression["application_skills"] = max(0, skill_progression["overall_performance"] + overall_trend)
            skill_progression["critical_thinking"] = max(0, skill_progression["overall_performance"] + overall_trend * 1.5)
        
        return skill_progression