"""Database models package for DRYAD backend"""

# Import all models from the main models file using importlib to avoid conflicts with models/ subdirectory
import importlib.util
import sys
import os

# Add current directory to path if not already there
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

# Import the models module directly from the file
spec = importlib.util.spec_from_file_location("models", os.path.join(os.path.dirname(__file__), "models.py"))
models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_module)

# Export all models from the models module
User = models_module.User
RefreshToken = models_module.RefreshToken
Conversation = models_module.Conversation
Message = models_module.Message
Document = models_module.Document
DocumentChunk = models_module.DocumentChunk
DocumentAnalytics = models_module.DocumentAnalytics
SearchAnalytics = models_module.SearchAnalytics
UserEngagement = models_module.UserEngagement
DocumentVersion = models_module.DocumentVersion
DocumentChangeLog = models_module.DocumentChangeLog
SearchQuery = models_module.SearchQuery
AgentInteraction = models_module.AgentInteraction
MultiModalContent = models_module.MultiModalContent
Organization = models_module.Organization
ClientApplication = models_module.ClientApplication
SharedKnowledge = models_module.SharedKnowledge

# Export all models for easy access
__all__ = [
    # Main models
    'User', 'RefreshToken', 'Conversation', 'Message', 'Document', 'DocumentChunk',
    'DocumentAnalytics', 'SearchAnalytics', 'UserEngagement', 'DocumentVersion',
    'DocumentChangeLog', 'SearchQuery', 'AgentInteraction', 'MultiModalContent',
    'Organization', 'ClientApplication', 'SharedKnowledge',
    
    # Tool registry models
    'ToolRegistry', 'ToolPermission', 'ToolSession', 'ToolExecution',
    'MemoryContext', 'ErrorLog'
]

# Lazy import for tool registry models to avoid circular dependencies
def __getattr__(name):
    """Lazily import tool registry models"""
    if name in ['ToolRegistry', 'ToolPermission', 'ToolSession', 'ToolExecution', 'MemoryContext', 'ErrorLog']:
        from .models.tool_registry import (
            ToolRegistry, ToolPermission, ToolSession, ToolExecution,
            MemoryContext, ErrorLog
        )
        globals()[name] = locals()[name]
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
