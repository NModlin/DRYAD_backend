"""
DRYAD.AI Python SDK

The official Python SDK for the DRYAD.AI platform - a comprehensive AI backend
with multi-agent workflows, vector search, multimodal processing, and real-time capabilities.

Features:
- Async/await support with full type safety
- Multi-agent workflow orchestration
- Vector search and RAG capabilities
- Multimodal processing (text, audio, video, images)
- Real-time WebSocket communication
- GraphQL integration
- Comprehensive error handling with automatic retries
- Connection pooling and resource management

Example:
    >>> import asyncio
    >>> from dryad_ai import DRYAD.AIClient
    >>>
    >>> async def main():
    ...     async with DRYAD.AIClient() as client:
    ...         response = await client.invoke_agent("Hello, AI!")
    ...         print(response['output'])
    >>>
    >>> asyncio.run(main())
"""

import os
from typing import Optional

from .client import DRYAD.AIClient
from .exceptions import (
    DRYAD.AIError,
    APIError,
    ValidationError,
    RateLimitError,
    AuthenticationError,
    ConnectionError,
    TimeoutError
)
from .models import (
    Conversation,
    Message,
    Document,
    Agent,
    Task,
    SystemHealth,
    MultiAgentWorkflow,
    VectorSearchResult,
    MultiModalContent
)

# Version information
__version__ = "1.0.0-beta.1"
__author__ = "DRYAD.AI Team"
__email__ = "support@DRYAD.AI.com"
__license__ = "MIT"
__url__ = "https://github.com/your-org/DRYAD_backend"

# Default configuration from environment
DEFAULT_BASE_URL = os.getenv("GREMLINS_AI_BASE_URL", "http://localhost:8000")
DEFAULT_API_KEY = os.getenv("GREMLINS_AI_API_KEY")
DEFAULT_TIMEOUT = int(os.getenv("GREMLINS_AI_TIMEOUT", "30"))

def create_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: Optional[int] = None,
    **kwargs
) -> DRYAD.AIClient:
    """
    Create a DRYAD.AI client with default configuration.

    Args:
        base_url: Base URL for the DRYAD.AI API (defaults to env var or localhost)
        api_key: API key for authentication (defaults to env var)
        timeout: Request timeout in seconds (defaults to env var or 30)
        **kwargs: Additional client configuration options

    Returns:
        Configured DRYAD.AIClient instance

    Example:
        >>> client = create_client()
        >>> # or with custom configuration
        >>> client = create_client(base_url="https://api.DRYAD.AI.com", timeout=60)
    """
    return DRYAD.AIClient(
        base_url=base_url or DEFAULT_BASE_URL,
        api_key=api_key or DEFAULT_API_KEY,
        timeout=timeout or DEFAULT_TIMEOUT,
        **kwargs
    )

# Public API
__all__ = [
    # Main client
    "DRYAD.AIClient",
    "create_client",

    # Exceptions
    "DRYAD.AIError",
    "APIError",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "ConnectionError",
    "TimeoutError",

    # Models
    "Conversation",
    "Message",
    "Document",
    "Agent",
    "Task",
    "SystemHealth",
    "MultiAgentWorkflow",
    "VectorSearchResult",
    "MultiModalContent",

    # Configuration
    "DEFAULT_BASE_URL",
    "DEFAULT_API_KEY",
    "DEFAULT_TIMEOUT",
]
