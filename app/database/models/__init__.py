"""Database models subpackage - re-exports all models from main database module"""

# Import Base from the parent database module - CRITICAL for university endpoints
from app.database.database import Base

# Import all models directly from the parent database module to avoid circular imports
from app.database import (
    User, RefreshToken, Conversation, Message, Document, DocumentChunk,
    DocumentAnalytics, SearchAnalytics, UserEngagement, DocumentVersion,
    DocumentChangeLog, SearchQuery, AgentInteraction, MultiModalContent,
    Organization, ClientApplication, SharedKnowledge
)

# Re-export for easy access
__all__ = [
    # Include Base - CRITICAL for university endpoints
    'Base',
    'User', 'RefreshToken', 'Conversation', 'Message', 'Document', 'DocumentChunk',
    'DocumentAnalytics', 'SearchAnalytics', 'UserEngagement', 'DocumentVersion',
    'DocumentChangeLog', 'SearchQuery', 'AgentInteraction', 'MultiModalContent',
    'Organization', 'ClientApplication', 'SharedKnowledge'
]