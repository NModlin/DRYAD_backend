"""
The Lyceum: Self-Improvement Engine
DRYAD.AI Agent Evolution Architecture - Level 5

Professor agents that follow Analyze → Hypothesize → Experiment → Validate → Propose loop:
- Professor Agent: Meta-agent for autonomous improvement
- Analyzer: Performance analysis from Dojo results
- Hypothesis Generator: Improvement hypothesis generation
- Experiment Runner: Controlled experiments in Laboratory
- Validator: Statistical validation of improvements
- Proposal Generator: Validated improvement proposals
"""

from dryad.services.lyceum.professor_agent import ProfessorAgent

__all__ = [
    "ProfessorAgent",
]

