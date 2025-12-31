"""
Dialogue Schemas

Pydantic schemas for Dialogue API requests and responses.
Ported from TypeScript service interfaces.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.dryad.models.dialogue_message import MessageRole


class DialogueMessageResponse(BaseModel):
    """Schema for dialogue message response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    id: str = Field(..., description="Message ID")
    dialogue_id: str = Field(..., description="Dialogue ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    content_preview: Optional[str] = Field(None, description="Content preview")


class DialogueResponse(BaseModel):
    """Schema for dialogue response."""
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
    id: str = Field(..., description="Dialogue ID")
    branch_id: str = Field(..., description="Branch ID")
    oracle_used: str = Field(..., description="Oracle provider used")
    insights: Optional[Dict[str, List[str]]] = Field(None, description="Extracted insights")
    storage_path: Optional[str] = Field(None, description="Storage path")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    message_count: Optional[int] = Field(None, description="Number of messages")
    messages: List[DialogueMessageResponse] = Field(default_factory=list, description="Dialogue messages")


class ConsultationRequest(BaseModel):
    """Schema for oracle consultation request."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    branch_id: str = Field(..., description="Branch ID")
    query: str = Field(..., min_length=1, description="Query for the oracle")
    provider_id: str = Field(..., description="Oracle provider ID")
    save_dialogue: Optional[bool] = Field(True, description="Whether to save the dialogue")


class ConsultationMetadata(BaseModel):
    """Schema for consultation metadata."""
    
    provider: str = Field(..., description="Oracle provider")
    branch_id: str = Field(..., description="Branch ID")
    vessel_id: str = Field(..., description="Vessel ID")
    timestamp: datetime = Field(..., description="Consultation timestamp")


class ConsultationResponse(BaseModel):
    """Schema for consultation response."""
    
    formatted_prompt: str = Field(..., description="Formatted prompt sent to oracle")
    metadata: ConsultationMetadata = Field(..., description="Consultation metadata")


class ProcessResponseRequest(BaseModel):
    """Schema for processing oracle response."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    branch_id: str = Field(..., description="Branch ID")
    provider_id: str = Field(..., description="Oracle provider ID")
    raw_response: str = Field(..., min_length=1, description="Raw response from oracle")
    original_query: Optional[str] = Field(None, description="Original query")


class ParsedWisdom(BaseModel):
    """Schema for parsed wisdom from oracle response."""
    
    themes: List[str] = Field(default_factory=list, description="Identified themes")
    facts: List[str] = Field(default_factory=list, description="Extracted facts")
    decisions: List[str] = Field(default_factory=list, description="Identified decisions")
    questions: List[str] = Field(default_factory=list, description="Generated questions")
    insights: List[str] = Field(default_factory=list, description="Key insights")


class ProcessResponseResult(BaseModel):
    """Schema for process response result."""
    
    dialogue_id: str = Field(..., description="Created dialogue ID")
    parsed_wisdom: ParsedWisdom = Field(..., description="Parsed wisdom from response")
    message_count: int = Field(..., description="Number of messages in dialogue")


class ProviderInfo(BaseModel):
    """Schema for oracle provider information."""
    
    id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Provider name")
    description: Optional[str] = Field(None, description="Provider description")
    enabled: bool = Field(..., description="Whether provider is enabled")


class DialogueListResponse(BaseModel):
    """Schema for dialogue list response."""
    
    dialogues: List[DialogueResponse] = Field(..., description="List of dialogues")
    total: int = Field(..., description="Total number of dialogues")
    branch_id: str = Field(..., description="Branch ID")
