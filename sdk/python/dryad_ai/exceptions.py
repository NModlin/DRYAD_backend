"""
DRYAD.AI SDK Exceptions

Custom exception classes for the DRYAD.AI Python SDK.
"""

from typing import Optional, Dict, Any


class DRYAD.AIError(Exception):
    """Base exception class for all DRYAD.AI SDK errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class APIError(DRYAD.AIError):
    """Raised when the API returns an error response."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, response_data)
        self.status_code = status_code
        self.response_data = response_data or {}


class ValidationError(DRYAD.AIError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(message, {"validation_errors": validation_errors or []})
        self.validation_errors = validation_errors or []


class AuthenticationError(DRYAD.AIError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class RateLimitError(DRYAD.AIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(message, {"retry_after": retry_after})
        self.retry_after = retry_after


class ConnectionError(DRYAD.AIError):
    """Raised when connection to the API fails."""
    
    def __init__(self, message: str = "Connection failed"):
        super().__init__(message)


class TimeoutError(DRYAD.AIError):
    """Raised when a request times out."""
    
    def __init__(self, message: str = "Request timed out", timeout: Optional[int] = None):
        super().__init__(message, {"timeout": timeout})
        self.timeout = timeout


class WebSocketError(DRYAD.AIError):
    """Raised when WebSocket operations fail."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message, {"error_code": error_code})
        self.error_code = error_code


class GraphQLError(DRYAD.AIError):
    """Raised when GraphQL operations fail."""
    
    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message, {"graphql_errors": errors or []})
        self.graphql_errors = errors or []


class TaskError(DRYAD.AIError):
    """Raised when task execution fails."""
    
    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        task_status: Optional[str] = None
    ):
        super().__init__(message, {"task_id": task_id, "task_status": task_status})
        self.task_id = task_id
        self.task_status = task_status


class DocumentError(DRYAD.AIError):
    """Raised when document operations fail."""
    
    def __init__(self, message: str, document_id: Optional[str] = None):
        super().__init__(message, {"document_id": document_id})
        self.document_id = document_id


class ConversationError(DRYAD.AIError):
    """Raised when conversation operations fail."""
    
    def __init__(self, message: str, conversation_id: Optional[str] = None):
        super().__init__(message, {"conversation_id": conversation_id})
        self.conversation_id = conversation_id


class AgentError(DRYAD.AIError):
    """Raised when agent operations fail."""
    
    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        workflow_type: Optional[str] = None
    ):
        super().__init__(message, {"agent_name": agent_name, "workflow_type": workflow_type})
        self.agent_name = agent_name
        self.workflow_type = workflow_type


# Utility functions for error handling
def handle_http_error(response) -> None:
    """Handle HTTP response and raise appropriate exceptions."""
    if response.status_code == 400:
        error_data = response.json() if response.content else {}
        raise ValidationError(
            error_data.get("message", "Validation error"),
            error_data.get("details", [])
        )
    elif response.status_code == 401:
        raise AuthenticationError("Invalid API key or authentication failed")
    elif response.status_code == 403:
        raise AuthenticationError("Access forbidden")
    elif response.status_code == 404:
        raise APIError("Resource not found", status_code=404)
    elif response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        raise RateLimitError(
            "Rate limit exceeded",
            retry_after=int(retry_after) if retry_after else None
        )
    elif response.status_code >= 500:
        error_data = response.json() if response.content else {}
        raise APIError(
            f"Server error: {error_data.get('message', 'Internal server error')}",
            status_code=response.status_code,
            response_data=error_data
        )
    elif response.status_code >= 400:
        error_data = response.json() if response.content else {}
        raise APIError(
            f"API error {response.status_code}: {error_data.get('message', 'Unknown error')}",
            status_code=response.status_code,
            response_data=error_data
        )


def handle_websocket_error(message: dict) -> None:
    """Handle WebSocket error messages."""
    if message.get("type") == "error":
        error_code = message.get("error_code")
        error_message = message.get("message", "WebSocket error")
        raise WebSocketError(error_message, error_code)


def handle_graphql_error(response_data: dict) -> None:
    """Handle GraphQL error responses."""
    if "errors" in response_data:
        errors = response_data["errors"]
        error_messages = [error.get("message", "GraphQL error") for error in errors]
        raise GraphQLError(
            f"GraphQL errors: {'; '.join(error_messages)}",
            errors=errors
        )
