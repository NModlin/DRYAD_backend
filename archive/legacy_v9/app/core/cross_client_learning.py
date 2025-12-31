# app/core/cross_client_learning.py
"""
Cross-Client Learning Framework for DRYAD.AI.
Implements privacy-preserving knowledge sharing, federated learning, and differential privacy.
"""

import logging
import hashlib
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import numpy as np

from app.database.models import SharedKnowledge, ClientApplication, User
from app.core.vector_store import vector_store

logger = logging.getLogger(__name__)

class PrivacyFilter:
    """Handles data anonymization and privacy protection."""
    
    @staticmethod
    def anonymize_content(content: str, privacy_level: str = "public") -> str:
        """Anonymize content based on privacy level."""
        if privacy_level == "private":
            return "[PRIVATE_CONTENT]"
        elif privacy_level == "restricted":
            # Remove PII and sensitive information
            anonymized = content
            # Simple anonymization - in production, use more sophisticated methods
            anonymized = anonymized.replace("@", "[EMAIL]")
            anonymized = anonymized.replace("http", "[URL]")
            return anonymized
        else:  # public
            return content
    
    @staticmethod
    def add_differential_privacy_noise(data: List[float], epsilon: float = 1.0) -> List[float]:
        """Add differential privacy noise to numerical data."""
        if not data:
            return data
        
        # Add Laplace noise for differential privacy
        sensitivity = 1.0  # Adjust based on your data sensitivity
        scale = sensitivity / epsilon
        
        noisy_data = []
        for value in data:
            noise = np.random.laplace(0, scale)
            noisy_data.append(value + noise)
        
        return noisy_data
    
    @staticmethod
    def hash_content(content: str) -> str:
        """Create a hash of content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()


class KnowledgeAggregator:
    """Aggregates knowledge across clients while preserving privacy."""
    
    def __init__(self):
        self.privacy_filter = PrivacyFilter()
    
    async def contribute_learning(
        self,
        client_id: str,
        interaction_data: Dict[str, Any],
        db: AsyncSession,
        privacy_level: str = "public"
    ) -> bool:
        """Contribute anonymized learning data to shared knowledge."""
        try:
            content = interaction_data.get("content", "")
            content_type = interaction_data.get("type", "interaction")
            category = interaction_data.get("category", "general")
            
            # Anonymize content
            anonymized_content = self.privacy_filter.anonymize_content(content, privacy_level)
            content_hash = self.privacy_filter.hash_content(content)
            
            # Check if this content already exists
            existing_stmt = select(SharedKnowledge).where(
                SharedKnowledge.content_hash == content_hash
            )
            result = await db.execute(existing_stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update contributing clients
                contributing_clients = existing.contributing_clients or []
                if client_id not in contributing_clients:
                    contributing_clients.append(client_id)
                    existing.contributing_clients = contributing_clients
                    existing.access_count += 1
                    await db.commit()
                return True
            
            # Create embedding if content is substantial
            embedding_vector = None
            if len(anonymized_content) > 50:  # Only embed substantial content
                try:
                    # Generate embedding using vector store
                    embedding = await vector_store.generate_embedding(anonymized_content)
                    if embedding:
                        # Add differential privacy noise to embedding
                        noisy_embedding = self.privacy_filter.add_differential_privacy_noise(
                            embedding, epsilon=1.0
                        )
                        embedding_vector = noisy_embedding
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")
            
            # Create shared knowledge entry
            shared_knowledge = SharedKnowledge(
                content_hash=content_hash,
                content_type=content_type,
                anonymized_content=anonymized_content,
                embedding_vector=embedding_vector,
                privacy_level=privacy_level,
                contributing_clients=[client_id],
                category=category,
                confidence_score=interaction_data.get("confidence", 0.5),
                access_count=1
            )
            
            db.add(shared_knowledge)
            await db.commit()
            
            logger.info(f"Knowledge contributed by client {client_id}: {content_type}/{category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to contribute learning: {e}")
            await db.rollback()
            return False
    
    async def get_shared_insights(
        self,
        client_id: str,
        query: str,
        db: AsyncSession,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant shared insights excluding client's own contributions."""
        try:
            # Build query
            stmt = select(SharedKnowledge).where(
                and_(
                    SharedKnowledge.privacy_level == "public",
                    ~SharedKnowledge.contributing_clients.contains([client_id])
                )
            )
            
            if category:
                stmt = stmt.where(SharedKnowledge.category == category)
            
            # If we have a query, try semantic search first
            if query and len(query) > 10:
                try:
                    # Generate query embedding
                    query_embedding = await vector_store.generate_embedding(query)
                    if query_embedding:
                        # Find similar embeddings (simplified - in production use proper vector search)
                        stmt = stmt.where(SharedKnowledge.embedding_vector.isnot(None))
                        stmt = stmt.order_by(SharedKnowledge.confidence_score.desc())
                except Exception as e:
                    logger.warning(f"Semantic search failed, using text search: {e}")
                    # Fallback to text search
                    stmt = stmt.where(SharedKnowledge.anonymized_content.contains(query))
            
            stmt = stmt.limit(limit)
            
            result = await db.execute(stmt)
            insights = result.scalars().all()
            
            # Format insights
            formatted_insights = []
            for insight in insights:
                formatted_insights.append({
                    "id": insight.id,
                    "content": insight.anonymized_content,
                    "type": insight.content_type,
                    "category": insight.category,
                    "confidence": insight.confidence_score,
                    "access_count": insight.access_count,
                    "created_at": insight.created_at.isoformat() if insight.created_at else None
                })
            
            logger.info(f"Retrieved {len(formatted_insights)} shared insights for client {client_id}")
            return formatted_insights
            
        except Exception as e:
            logger.error(f"Failed to get shared insights: {e}")
            return []
    
    async def analyze_learning_patterns(
        self,
        client_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze learning patterns and provide insights."""
        try:
            # Get recent shared knowledge
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            stmt = select(SharedKnowledge).where(
                and_(
                    SharedKnowledge.created_at >= cutoff_date,
                    ~SharedKnowledge.contributing_clients.contains([client_id])
                )
            )
            
            result = await db.execute(stmt)
            recent_knowledge = result.scalars().all()
            
            # Analyze patterns
            categories = {}
            content_types = {}
            total_insights = len(recent_knowledge)
            
            for knowledge in recent_knowledge:
                # Count by category
                category = knowledge.category or "general"
                categories[category] = categories.get(category, 0) + 1
                
                # Count by content type
                content_type = knowledge.content_type
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            # Calculate trends
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            top_content_types = sorted(content_types.items(), key=lambda x: x[1], reverse=True)[:5]
            
            analysis = {
                "total_insights": total_insights,
                "analysis_period_days": days,
                "top_categories": top_categories,
                "top_content_types": top_content_types,
                "category_distribution": categories,
                "content_type_distribution": content_types,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Learning pattern analysis completed for client {client_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze learning patterns: {e}")
            return {"error": str(e)}


class FederatedLearningManager:
    """Manages federated learning across clients."""
    
    def __init__(self):
        self.knowledge_aggregator = KnowledgeAggregator()
    
    async def aggregate_client_insights(
        self,
        client_insights: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Aggregate insights from multiple clients."""
        try:
            aggregated_patterns = {}
            total_clients = len(client_insights)
            
            for insight in client_insights:
                client_id = insight.get("client_id")
                patterns = insight.get("patterns", {})
                
                for pattern_type, pattern_data in patterns.items():
                    if pattern_type not in aggregated_patterns:
                        aggregated_patterns[pattern_type] = []
                    aggregated_patterns[pattern_type].append(pattern_data)
            
            # Calculate aggregated statistics
            aggregated_stats = {}
            for pattern_type, pattern_list in aggregated_patterns.items():
                if pattern_list:
                    # Simple aggregation - in production, use more sophisticated methods
                    aggregated_stats[pattern_type] = {
                        "count": len(pattern_list),
                        "clients": total_clients,
                        "average": sum(pattern_list) / len(pattern_list) if isinstance(pattern_list[0], (int, float)) else None
                    }
            
            return {
                "aggregated_patterns": aggregated_stats,
                "participating_clients": total_clients,
                "aggregated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to aggregate client insights: {e}")
            return {"error": str(e)}


# Global instances
privacy_filter = PrivacyFilter()
knowledge_aggregator = KnowledgeAggregator()
federated_learning_manager = FederatedLearningManager()
