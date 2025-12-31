"""
RAG-Gym: Memory Guild Benchmark Suite
DRYAD.AI Agent Evolution Architecture - Level 4

Specialized benchmarks for evaluating Memory Guild capabilities:
1. Ingestion Accuracy - Correct extraction of entities and metadata
2. Retrieval Precision - Semantic search quality
3. Deduplication - Ability to detect duplicate content
4. Multi-hop Reasoning - Graph traversal for complex queries
5. Summarization Quality - Coherence and accuracy of summaries
6. Access Control - Policy enforcement correctness
"""

from app.services.dojo.rag_gym.ingestion_benchmark import IngestionBenchmark
from app.services.dojo.rag_gym.retrieval_benchmark import RetrievalBenchmark
from app.services.dojo.rag_gym.deduplication_benchmark import DeduplicationBenchmark

__all__ = [
    "IngestionBenchmark",
    "RetrievalBenchmark",
    "DeduplicationBenchmark",
]

