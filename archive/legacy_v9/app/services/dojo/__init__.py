"""
The Dojo: Evaluation Framework
DRYAD.AI Agent Evolution Architecture - Level 4

Provides quantitative measurement of agent performance through:
- Benchmark Registry: Standardized evaluation problems
- Evaluation Harness: Agent evaluation execution
- RAG-Gym: Specialized Memory Guild benchmarks
- Leaderboard: Performance ranking and comparison
"""

from app.services.dojo.benchmark_registry import BenchmarkRegistry
from app.services.dojo.evaluation_harness import EvaluationHarness

__all__ = [
    "BenchmarkRegistry",
    "EvaluationHarness",
]

