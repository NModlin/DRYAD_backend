# app/core/tools.py
import logging
import re
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Initialize the tool. This can be reused across the application.
search_tool = DuckDuckGoSearchRun()

class SearchInput(BaseModel):
    query: str = Field(description="The search query to execute.")

def sanitize_input(text: str) -> str:
    """
    Sanitize input text to prevent XSS and other security issues.
    Removes or escapes potentially dangerous HTML/script tags.
    """
    if not text:
        return text

    # Remove script tags and their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove other potentially dangerous tags
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
    for tag in dangerous_tags:
        text = re.sub(f'<{tag}[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(f'</{tag}>', '', text, flags=re.IGNORECASE)

    # Remove javascript: and data: URLs
    text = re.sub(r'javascript:[^"\s]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:[^"\s]*', '', text, flags=re.IGNORECASE)

    return text.strip()

def sanitize_output(text: str) -> str:
    """
    Sanitize output text to prevent XSS in search results.
    Removes script tags and other dangerous content from search results.
    """
    if not text:
        return text

    # Remove script tags and their content from search results
    text = re.sub(r'<script[^>]*>.*?</script>', '[SCRIPT_REMOVED]', text, flags=re.IGNORECASE | re.DOTALL)

    # Replace standalone script tags
    text = re.sub(r'<script[^>]*>', '[SCRIPT_REMOVED]', text, flags=re.IGNORECASE)
    text = re.sub(r'</script>', '[/SCRIPT_REMOVED]', text, flags=re.IGNORECASE)

    # Also remove any remaining script-like patterns
    text = re.sub(r'<script>', '[SCRIPT_REMOVED]', text, flags=re.IGNORECASE)
    text = re.sub(r'<script\s+[^>]*>', '[SCRIPT_REMOVED]', text, flags=re.IGNORECASE)

    return text

def explicit_web_search(query: str, explicit_request: bool = False) -> str:
    """
    EXPLICIT WEB SEARCH ONLY - NOT FOR AI REASONING FALLBACK

    This function performs web search ONLY when explicitly requested by users
    for web search functionality. It should NEVER be used as a fallback when
    AI reasoning fails or when local LLM is unavailable.

    Args:
        query: The search query string
        explicit_request: Must be True to confirm this is an explicit web search request

    Returns:
        Search results or error message

    Raises:
        RuntimeError: If used without explicit confirmation (prevents AI fallback usage)
    """
    if not explicit_request:
        raise RuntimeError(
            "Web search can only be used for explicit web search requests, "
            "not as a fallback for AI reasoning. Use local AI capabilities instead."
        )

    # Sanitize the input query
    sanitized_query = sanitize_input(query)
    logger.info(f"Executing EXPLICIT web search for: {sanitized_query}")

    try:
        # Perform the search
        results = search_tool.invoke(sanitized_query)

        # Sanitize the output to prevent XSS in search results
        sanitized_results = sanitize_output(results)

        return sanitized_results
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return "No web search results found"

# Legacy function name - deprecated, redirects to explicit function
def duckduckgo_search(query: str) -> str:
    """
    DEPRECATED: Use explicit_web_search() with explicit_request=True instead.

    This function is deprecated to prevent accidental use as AI reasoning fallback.
    For explicit web search functionality, use explicit_web_search(query, explicit_request=True).
    """
    logger.warning(
        f"duckduckgo_search() called with query '{query[:50]}...' - this function is deprecated. "
        "Use explicit_web_search() with explicit_request=True to confirm this is an explicit web search request."
    )
    raise RuntimeError(
        "duckduckgo_search() is deprecated to prevent AI fallback usage. "
        "Use explicit_web_search(query, explicit_request=True) for explicit web search requests."
    )

# In later phases, more tools will be added here.
# Example:
# def transcribe_video_audio(video_path: str) -> str: ...
